import concurrent.futures
import time
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
    with open("devices.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["devices"]

def process_static_device(device):
    ip = device["ip"]
    hostname = device.get("hostname", ip)
    print(f"\n=== Обрабатываем статику {hostname} ({ip}) ===")

    raw = collect_raw(device, command_type="static")
    if not raw:
        print(f"Не удалось собрать static для {ip}")
        return

    print(f"Собрано static: {list(raw.keys())}")

    device_obj = {
        "ip": ip,
        "hostname": hostname,
        "vendor": device["vendor"],
        "vlans": [],
        "interfaces": [],
        "svi": [],
        "version_info": {},
        "interfaces_config": []
    }

    # VLAN
    parser_vlan = get_parser(device["vendor"], "vlan")
    if parser_vlan and "show vlan" in raw:
        parsed = parser_vlan("show vlan", raw["show vlan"], device["vendor"])
        normalized = VlanNormalizer.normalize(parsed, device["vendor"])
        save_parsed(normalized, ip, "vlan")
        device_obj["vlans"] = normalized.get("vlans", [])

    # Interface brief
    parser_int = get_parser(device["vendor"], "interface_brief")
    if parser_int and "show interface brief" in raw:
        parsed = parser_int("show interface brief", raw["show interface brief"], device["vendor"])
        normalized = InterfaceNormalizer.normalize(parsed, device["vendor"])
        save_parsed(normalized, ip, "interface_brief")
        device_obj["interfaces"] = normalized.get("interfaces", [])

    # Version
    parser_ver = get_parser(device["vendor"], "version")
    if parser_ver and "show version" in raw:
        parsed = parser_ver("show version", raw["show version"], device["vendor"])
        normalized = VersionNormalizer.normalize(parsed, device["vendor"])
        save_parsed(normalized, ip, "version")
        device_obj["version_info"] = normalized

    # SVI
    parser_svi = get_parser(device["vendor"], "ip_interface")
    if parser_svi and "show ip interface brief" in raw:
        parsed = parser_svi("show ip interface brief", raw["show ip interface brief"], device["vendor"])
        normalized = SVINormalizer.normalize(parsed, device["vendor"])
        save_parsed(normalized, ip, "ip_interface")
        device_obj["svi"] = normalized.get("svi", [])

    # Running config
    parser_cfg = get_parser(device["vendor"], "running_config")
    if parser_cfg and "show running-config" in raw:
        parsed = parser_cfg("show running-config", raw["show running-config"], device["vendor"])
        normalized = ConfigNormalizer.normalize(parsed, device["vendor"])
        save_parsed(normalized, ip, "running_config")
        device_obj["interfaces_config"] = normalized.get("interfaces_config", [])

    # Сохраняем per-device snapshot
    snapshot = {
        "snapshot": {
            "id": datetime.utcnow().isoformat(),
            "type": "static_device",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "device_ip": ip,
            "device_hostname": hostname
        },
        "device": device_obj
    }

    save_snapshot(snapshot, identifier=ip)

def main():
    start_time = time.time()

    devices = load_devices()
    print(f"Загружено устройств для статики: {len(devices)}")

    if not devices:
        print("Нет устройств")
        return

    # Параллельный сбор
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_device = {executor.submit(process_static_device, device): device for device in devices}
        for future in concurrent.futures.as_completed(future_to_device):
            future.result()

    print(f"\nСбор статики завершён за {time.time() - start_time:.2f} секунд")

if __name__ == "__main__":
    main()