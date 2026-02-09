from typing import List, Dict, Optional
from pydantic import ValidationError
from src.models.host import Host
from src.filters.port_filters import is_ignored_port  # ← правильный импорт

def merge_hosts(
    mac_entries: List[Dict],
    arp_entries: List[Dict],
    dhcp_leases: List[Dict] = None,
    static_interfaces: Dict[str, Dict[str, str]] = None  # {hostname: {port: mode}}
) -> List[Dict]:
    """
    Основной merge по MAC:
    - берём MAC-table как основу (vlan, port, device)
    - фильтруем только access-порты (через port_filter)
    - добавляем IP из ARP
    - обогащаем description/type/status из DHCP
    """
    if dhcp_leases is None:
        dhcp_leases = []
    if static_interfaces is None:
        static_interfaces = {}  # пока без статических mode — можно загрузить позже

    hosts_dict = {}

    # 1. MAC-table (основной источник)
    for entry in mac_entries:
        mac = entry["mac"]
        port = entry["port"]
        device_ip = entry["device_ip"]
        device_hostname = entry["device_hostname"]

        # Фильтрация порта — вызываем функцию из port_filter
        if is_ignored_port(device_ip, port):
            continue  # игнорируем этот порт

        hosts_dict[mac] = {
            "mac": mac,
            "vlan": entry["vlan"],
            "port": port,
            "device_ip": device_ip,
            "device_hostname": device_hostname,
            "source": ["mac_table"]
        }

    # 2. ARP (добавляем IP)
    for entry in arp_entries:
        mac = entry["mac"]
        ip = entry["ip"]
        if mac in hosts_dict:
            hosts_dict[mac]["ip"] = ip
            if "arp" not in hosts_dict[mac]["source"]:
                hosts_dict[mac]["source"].append("arp")

    # 3. DHCP (обогащаем description, type, status) — пока заглушка
    for lease in dhcp_leases:
        mac = lease.get("mac")
        if mac and mac in hosts_dict:
            hosts_dict[mac]["description"] = lease.get("description")
            hosts_dict[mac]["type"] = lease.get("type", "lease")
            hosts_dict[mac]["status"] = lease.get("status", "active")
            if "dhcp" not in hosts_dict[mac]["source"]:
                hosts_dict[mac]["source"].append("dhcp")

    # Валидация и создание объектов Host
    valid_hosts = []
    for data in hosts_dict.values():
        try:
            host = Host(**data)
            valid_hosts.append(host.model_dump())
        except ValidationError as e:
            print(f"Ошибка валидации хоста {data.get('mac')}: {e}")

    print(f"Сформировано валидных хостов: {len(valid_hosts)}")
    return valid_hosts