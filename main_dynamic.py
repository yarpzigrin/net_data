import json
import yaml
from datetime import datetime
from pathlib import Path
import concurrent.futures
import time

from src.collectors.ssh_collector import collect_raw
from src.collectors.win_dhcp_collector import collect_dhcp_raw, save_dhcp_raw
from src.parsers.registry import get_parser
from src.normalizer.mac_table import MacTableNormalizer
from src.normalizer.arp import ArpNormalizer
from src.normalizer.dhcp import DhcpNormalizer
from src.merge.hosts_merge import merge_hosts
from src.storage.file import save_parsed, save_dynamic_snapshot

def load_devices():
    with open("devices.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["devices"]

def load_dhcp_servers():
    path = Path("config/servers.yaml")
    if not path.exists():
        print("config/servers.yaml не найден — DHCP отключён")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        print("config/servers.yaml пустой — DHCP отключён")
        return []

    return data.get("DHCP_servers", [])

def process_device(device):
    ip = device["ip"]
    hostname = device.get("hostname", ip)
    print(f"\n=== Обрабатываем {hostname} ({ip}) ===")

    raw = collect_raw(device, command_type="dynamic")
    if not raw:
        print(f"Не удалось собрать raw для {ip}")
        return [], []

    print(f"Собрано raw: {list(raw.keys())}")

    macs = []
    arps = []

    # MAC со всех устройств
    parser_mac = get_parser(device["vendor"], "mac_address_table")
    if parser_mac and "show mac address-table" in raw:
        parsed_mac = parser_mac(
            "show mac address-table",
            raw["show mac address-table"],
            device["vendor"],
            device_ip=ip,
            device_hostname=hostname
        )
        normalized_mac = MacTableNormalizer.normalize(parsed_mac, device["vendor"])
        macs = normalized_mac.get("mac_entries_normalized", [])

        # Добавляем информацию об устройстве
        for m in macs:
            m["device_ip"] = ip
            m["device_hostname"] = hostname

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
            print(f"{ip} — ARP записей: {len(arps)}")
            save_parsed(normalized_arp, ip, "arp")
        else:
            print(f"{ip} — ARP не собран (нет парсера)")

    return macs, arps

def main():
    start_time = time.time()

    devices = load_devices()
    print(f"Загружено устройств: {len(devices)}")

    if not devices:
        print("Нет устройств")
        return

    all_mac_entries = []
    all_arp_entries = []

    # Параллельный сбор данных по устройствам
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_device = {executor.submit(process_device, device): device for device in devices}
        for future in concurrent.futures.as_completed(future_to_device):
            device_macs, device_arps = future.result()
            all_mac_entries.extend(device_macs)
            all_arp_entries.extend(device_arps)

    print(f"Всего собрано MAC: {len(all_mac_entries)}, ARP: {len(all_arp_entries)}")

    # DHCP — сбор сырых данных и парсинг
    dhcp_servers = load_dhcp_servers()

    dhcp_raw_dir = Path("data/raw/dhcp")
    dhcp_parsed_leases_dir = Path("data/parsed/dynamic/dhcp_leases")
    dhcp_parsed_reservations_dir = Path("data/parsed/dynamic/dhcp_reservations")

    dhcp_parsed_leases_dir.mkdir(parents=True, exist_ok=True)
    dhcp_parsed_reservations_dir.mkdir(parents=True, exist_ok=True)

    if not dhcp_servers:
        print("DHCP-серверы не загружены — пропуск DHCP")
    else:
        for srv in dhcp_servers:
            srv_ip = srv["ip"]
            print(f"\n=== Собираем DHCP с сервера {srv_ip} ({srv.get('location', 'unknown')}) ===")

            leases_text, reservations_text = collect_dhcp_raw(srv_ip)
            save_dhcp_raw(leases_text, reservations_text, srv_ip)

            print(f"=== Парсим DHCP для сервера {srv_ip} ===")

            parsed_leases = get_parser("nateks", "dhcp_leases")("dhcp_leases", leases_text, "nateks")
            normalized_leases = DhcpNormalizer.normalize_leases(parsed_leases, "nateks")
            save_parsed(normalized_leases, srv_ip, "dhcp_leases")

            parsed_reservations = get_parser("nateks", "dhcp_reservations")("dhcp_reservations", reservations_text, "nateks")
            normalized_reservations = DhcpNormalizer.normalize_reservations(parsed_reservations, "nateks")
            save_parsed(normalized_reservations, srv_ip, "dhcp_reservations")

            print(f"[DHCP] Готово для {srv_ip}")

    # Merge — пока заглушка (раскомментируй, когда DHCP будет готов к merge)
    hosts = merge_hosts(all_mac_entries, all_arp_entries, dhcp_leases=[])  # dhcp_leases=[]

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

    end_time = time.time()
    print(f"\nПолный цикл завершён за {end_time - start_time:.2f} секунд")

if __name__ == "__main__":
    main()