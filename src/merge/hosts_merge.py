from typing import List, Dict, Optional
from pydantic import ValidationError
from src.models.host import Host
from src.filters.port_filters import is_ignored_port

def merge_hosts(
    mac_entries: List[Dict],
    arp_entries: List[Dict],
    dhcp_leases: List[Dict] = None,
    static_interfaces: Dict[str, Dict[str, str]] = None
) -> List[Dict]:
    """
    Merge по MAC:
    - Основа: MAC-table (vlan, port, device)
    - Фильтр access-портов (port_filter)
    - Логика type: если mac-ip в DHCP — lease/reserved; если в ARP/MAC — static; нет — unknown
    - Логика status: active если mac-ip пара (L2+L3); MAC без ARP — unknown
    - Логика ip: из ARP/DHCP; нет — "unknown"
    - DHCP обогащает description/type/status
    """
    if dhcp_leases is None:
        dhcp_leases = []
    if static_interfaces is None:
        static_interfaces = {}

    hosts_dict = {}

    # 1. MAC-table (основной источник)
    for entry in mac_entries:
        mac = entry["mac"]
        port = entry["port"]
        device_ip = entry["device_ip"]
        device_hostname = entry["device_hostname"]

        if is_ignored_port(device_ip, port):
            continue

        hosts_dict[mac] = {
            "mac": mac,
            "vlan": entry["vlan"],
            "port": port,
            "device_ip": device_ip,
            "device_hostname": device_hostname,
            "ip": "unknown",  # по умолчанию
            "type": "unknown",  # по умолчанию
            "status": "unknown",  # по умолчанию
            "source": ["mac_table"]
        }

    # 2. ARP (добавляем IP, обновляем type/status)
    for entry in arp_entries:
        mac = entry["mac"]
        ip = entry["ip"]
        if mac in hosts_dict:
            hosts_dict[mac]["ip"] = ip
            hosts_dict[mac]["source"].append("arp")
            hosts_dict[mac]["status"] = "active"  # mac-ip пара → active
            hosts_dict[mac]["type"] = "static"  # если нет DHCP — static

    # 3. DHCP (обогащаем, приоритет DHCP для type)
    for lease in dhcp_leases:
        mac = lease.get("mac")
        if mac in hosts_dict:
            hosts_dict[mac]["description"] = lease.get("description")
            hosts_dict[mac]["type"] = lease.get("type", "lease")  # lease/reserved
            hosts_dict[mac]["ip"] = lease.get("ip") or hosts_dict[mac]["ip"]
            hosts_dict[mac]["status"] = "reserved(inactive)" if lease.get("type") == "reserved" and not lease.get("active") else "active"
            hosts_dict[mac]["source"].append("dhcp")

    # Валидация и model_dump
    valid_hosts = []
    for data in hosts_dict.values():
        try:
            host = Host(**data)
            valid_hosts.append(host.model_dump())
        except ValidationError as e:
            print(f"Ошибка валидации хоста {data.get('mac')}: {e}")

    print(f"Сформировано валидных хостов: {len(valid_hosts)}")
    return valid_hosts