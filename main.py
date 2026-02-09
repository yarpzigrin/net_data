import json
import yaml
from pathlib import Path
from datetime import datetime

from src.collectors.ssh_collector import collect_raw
from src.parsers.registry import get_parser
from src.normalizer.vlan import VlanNormalizer
from src.normalizer.interface import InterfaceNormalizer
from src.normalizer.version import VersionNormalizer
from src.normalizer.svi import SVINormalizer
from src.normalizer.config import ConfigNormalizer
from src.storage.file import save_parsed, save_snapshot

def load_devices():
    with open("devices.yaml", "r") as f:
        data = yaml.safe_load(f)
    return data["devices"]

def main():
    devices = load_devices()
    print(f"Загружено устройств: {len(devices)}")

    if not devices:
        print("Нет устройств")
        return

    # Глобальный словарь для VLAN: {vlan_id: {vlan_data, devices: []}}
    global_vlans_dict = {}

    for device in devices:
        ip = device["ip"]
        hostname = device.get("hostname", ip)
        print(f"\n=== Обрабатываем {hostname} ({ip}) ===")

        try:
            # Сбор raw
            raw_static = collect_raw(device, command_type="static")
            if not raw_static:
                print(f"Не удалось собрать static для {ip}")
                continue

            print(f"Собрано static: {list(raw_static.keys())}")

            # Инициализация device_obj
            device_obj = {
                "ip": ip,
                "hostname": hostname,
                "vendor": device["vendor"],
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "id_number": device.get("id_number"),
                "firmware": device.get("firmware"),
                "build": device.get("build"),
                "vend_ID": device.get("vend_ID"),
                "product_ID": device.get("product_ID"),
                "location": device.get("location", "unknown"),
                "status": "reachable",
                "vlans": [],
                "interfaces": [],
                "lldp_neighbors": [],
                "svi": [],
                "config": {}
            }

            # Парсинг и нормализация VLAN
            parser_vlan = get_parser(device["vendor"], "vlan")
            if parser_vlan:
                parsed_vlan = parser_vlan("show vlan", raw_static.get("show vlan", ""), device["vendor"])
                print(f"Разобрано VLAN: {len(parsed_vlan.get('vlans', []))}")
                normalized_vlan = VlanNormalizer.normalize(parsed_vlan, device["vendor"])
                print(f"Нормализовано VLAN: {len(normalized_vlan.get('vlans', []))}")
                save_parsed(normalized_vlan, ip, "vlan")
                device_obj["vlans"] = [
                    v for v in normalized_vlan.get("vlans", [])
                    if v["vlan_id"] != "1" and v["vlan_id"] != 1  # на всякий случай проверяем и строку, и число
                ]
                
                # Добавляем в глобальный словарь
                for v in device_obj["vlans"]:
                    vlan_id = v["vlan_id"]
                    if vlan_id == "1":  # игнорируем VLAN 1
                        continue

                    if vlan_id not in global_vlans_dict:
                        global_vlans_dict[vlan_id] = {
                            "vlan_id": vlan_id,
                            "name": v["name"],
                            "status": v["status"],
                            "devices": []
                        }

                    global_vlans_dict[vlan_id]["devices"].append({
                        "ip": ip,
                        "hostname": hostname,
                        "ports": v.get("ports", [])
                    })
            else:
                print("Парсер VLAN не найден")

            # Парсинг и нормализация interface brief
            parser_intf = get_parser(device["vendor"], "interface_brief")
            if parser_intf:
                parsed_intf = parser_intf("show interface brief", raw_static.get("show interface brief", ""), device["vendor"])
                print(f"Разобрано интерфейсов: {len(parsed_intf.get('interfaces', []))}")
                normalized_intf = InterfaceNormalizer.normalize(parsed_intf, device["vendor"])
                print(f"Нормализовано интерфейсов: {len(normalized_intf.get('interfaces', []))}")
                save_parsed(normalized_intf, ip, "interface_brief")
                device_obj["interfaces"] = normalized_intf.get("interfaces", [])
            else:
                print("Парсер interface brief не найден")

            # Парсинг и нормализация show version
            parser_version = get_parser(device["vendor"], "version")
            if parser_version:
                parsed_version = parser_version("show version", raw_static.get("show version", ""), device["vendor"])
                print("Разобрано version_info:", parsed_version)
                normalized_version = VersionNormalizer.normalize(parsed_version, device["vendor"])
                print("Нормализовано version:", normalized_version)
                save_parsed(normalized_version, ip, "version")

                for key, value in normalized_version.items():
                    if value:
                        device_obj[key] = value
            else:
                print("Парсер для version не найден")

            # Парсинг и нормализация show ip interface brief
            parser_svi = get_parser(device["vendor"], "ip_interface")
            if parser_svi:
                parsed_svi = parser_svi("show ip interface brief", raw_static.get("show ip interface brief", ""), device["vendor"])
                print(f"Разобрано SVI: {len(parsed_svi.get('svi', []))}")
                normalized_svi = SVINormalizer.normalize(parsed_svi, device["vendor"])
                print(f"Нормализовано SVI: {len(normalized_svi.get('svi', []))}")
                save_parsed(normalized_svi, ip, "ip_interface")

                for svi in normalized_svi.get("svi", []):
                    vlan_num = int(svi["interface"].replace("VLAN", ""))
                    for v in device_obj["vlans"]:
                        if v["vlan_id"] == vlan_num:
                            svi["description"] = v["name"]
                            break

                device_obj["svi"] = normalized_svi.get("svi", [])
            else:
                print("Парсер для ip interface brief не найден")

            # Парсинг running-config только для обогащения интерфейсов
            parser_config = get_parser(device["vendor"], "running_config")
            if parser_config:
                parsed_config = parser_config("show running-config", raw_static.get("show running-config", ""), device["vendor"])
                print("Разобрано интерфейсов из конфига:", len(parsed_config.get("interfaces_config", [])))

                normalized_config = ConfigNormalizer.normalize(parsed_config, device["vendor"])
                print("Нормализовано конфигов интерфейсов:", len(normalized_config.get("interfaces_config_normalized", [])))

                save_parsed(normalized_config, ip, "running_config")

                config_intfs = {intf["name"].lower(): intf for intf in normalized_config.get("interfaces_config_normalized", [])}

                enriched_count = 0
                for intf in device_obj["interfaces"]:
                    config_key = intf["name"].lower()
                    if config_key in config_intfs:
                        cfg = config_intfs[config_key]
                        intf["mode"] = cfg["mode"]
                        intf["allowed_vlans"] = cfg["allowed_vlans"]
                        intf["untagged_vlans"] = cfg["untagged_vlans"]
                        intf["pvid"] = cfg["pvid"] if cfg["pvid"] else ("1" if cfg["mode"] == "trunk" else None)
                        intf["voice_vlan_mode"] = cfg["voice_vlan_mode"]
                        intf["voice_vlan_vid"] = cfg["voice_vlan_vid"]
                        intf.pop("vlan", None)
                        enriched_count += 1

                print(f"Обогащено интерфейсов из конфига: {enriched_count}")
            else:
                print("Парсер для running-config не найден")

            # Формируем snapshot для текущего устройства
            snapshot = {
                "snapshot": {
                    "id": datetime.utcnow().isoformat(),
                    "type": "static_test",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "schema_version": "1.0",
                    "device_ip": ip,
                    "device_hostname": hostname,
                    "summary": {
                        "vlans_total": len(device_obj["vlans"]),
                        "interfaces_total": len(device_obj["interfaces"]),
                        "svi_total": len(device_obj.get("svi", [])),
                        "enriched_interfaces": enriched_count,
                        "hosts_total": 0,
                        "errors": 0
                    }
                },
                "device": device_obj,
                "vlans": device_obj["vlans"],
                "hosts": []
            }

            save_snapshot(snapshot, identifier=ip)

        except Exception as e:
            print(f"Ошибка обработки {hostname} ({ip}): {e}")
            continue

    # После обработки всех устройств — сохраняем глобальные VLAN
    global_vlans = list(global_vlans_dict.values())

    global_vlans_snapshot = {
        "snapshot": {
            "id": datetime.utcnow().isoformat(),
            "type": "global_vlans",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "schema_version": "1.0",
            "devices_count": len(devices),
            "vlans_total": len(global_vlans)
        },
        "vlans": global_vlans
    }

    global_path = Path("data/snapshots/global_vlans_snapshot.json")
    global_path.parent.mkdir(parents=True, exist_ok=True)
    global_path.write_text(json.dumps(global_vlans_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Сохранён глобальный VLAN-снимок: {global_path} (уникальных VLAN: {len(global_vlans)})")

if __name__ == "__main__":
    main()