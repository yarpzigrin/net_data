import json
import yaml
from datetime import datetime
from pathlib import Path

from src.collectors.ssh_collector import collect_raw
# from src.collectors.win_dhcp_collector import collect_dhcp  # подключим позже
from src.parsers.registry import get_parser
from src.normalizer.mac_table import MacTableNormalizer
from src.normalizer.arp import ArpNormalizer
# from src.merge.hosts_merge import merge_hosts  # подключим позже
from src.storage.file import save_parsed, save_dynamic_snapshot
from src.merge.hosts_merge import merge_hosts

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

    all_mac_entries = []
    all_arp_entries = []

    for device in devices:
        ip = device["ip"]
        print(f"\n=== Обрабатываем {device.get('hostname', ip)} ({ip}) ===")

        raw = collect_raw(device, command_type="dynamic")
        if not raw:
            print(f"Не удалось собрать raw для {ip}")
            continue

        print(f"Собрано raw: {list(raw.keys())}")

    # MAC со всех устройств
        parser_mac = get_parser(device["vendor"], "mac_address_table")
        if parser_mac and "show mac address-table" in raw:
            parsed_mac = parser_mac("show mac address-table", raw["show mac address-table"], device["vendor"], device_ip=ip, device_hostname=device.get("hostname", ip))
            normalized_mac = MacTableNormalizer.normalize(parsed_mac, device["vendor"])
            macs = normalized_mac.get("mac_entries_normalized", [])

            # ← Вот этот блок — добавляем информацию об устройстве
            for m in macs:
                m["device_ip"] = ip
                m["device_hostname"] = device.get("hostname", ip)

            all_mac_entries.extend(macs)
            print(f"{ip} — MAC записей: {len(macs)}")
            save_parsed(normalized_mac, ip, "mac_address_table")
        else:
            print(f"{ip} — MAC не собран (нет парсера или команды)")

        # ARP только с core
        if device.get("group") == "core" and "show arp" in raw:
            parser_arp = get_parser(device["vendor"], "arp")
            if parser_arp:
                parsed_arp = parser_arp("show arp", raw["show arp"], device["vendor"])
                normalized_arp = ArpNormalizer.normalize(parsed_arp, device["vendor"])
                arps = normalized_arp.get("arp_entries_normalized", [])
                all_arp_entries.extend(arps)
                print(f"{ip} — ARP записей: {len(arps)}")
                save_parsed(normalized_arp, ip, "arp")  # сохраняем parsed ARP
            else:
                print(f"{ip} — ARP не собран (нет парсера)")

    # DHCP — пока заглушка
    dhcp_leases = []

    # Merge — пока заглушка
    hosts = merge_hosts(all_mac_entries, all_arp_entries, dhcp_leases=[])

    # Формируем snapshot
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    snapshot = {
        "snapshot": {
            "id": datetime.utcnow().isoformat(),
            "type": "dynamic_hosts",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "schema_version": "1.0",
            "devices_count": len(devices),
            "hosts_count": len(hosts),
            "sources": ["mac_address_table", "arp", "dhcp"]
        },
        "hosts": hosts
    }

    save_dynamic_snapshot(snapshot, snapshot_type="hosts")

if __name__ == "__main__":
    main()