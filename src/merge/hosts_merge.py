from typing import List, Dict, Optional
from pydantic import ValidationError
from src.models.host import Host

def merge_hosts(
    mac_entries: List[Dict],
    arp_entries: List[Dict],
    dhcp_leases: List[Dict] = None
) -> List[Dict]:
    """
    Merge по MAC:
    - Основа — MAC-table (vlan, port, device)
    - Фильтр портов (port_filter)
    - status — строго по ARP (active если mac-ip пара есть, иначе unknown)
    - type — lease/reserved по DHCP, static если ARP+MAC без DHCP, unknown если только MAC
    - DHCP обогащает description/hostname/dhcp_server/lease_end
    """
    if dhcp_leases is None:
        dhcp_leases = []

    hosts_dict = {}

    # 1. MAC-table — основа
    for entry in mac_entries:
        mac = entry["mac"]
        port = entry["port"]
        device_ip = entry["device_ip"]
        device_hostname = entry["device_hostname"]

        hosts_dict[mac] = {
            "mac": mac,
            "vlan": entry.get("vlan"),
            "port": entry.get("port"),
            "device_ip": device_ip,
            "device_hostname": device_hostname,
            "ip": "unknown",
            "status": "unknown",
            "type": "unknown",
            "description": None,
            "hostname": None,
            "dhcp_server": None,
            "lease_end": None,
            "source": ["mac_table"]
        }

    # 2. ARP — главный источник статуса и IP
    for entry in arp_entries:
        mac = entry["mac"]
        ip = entry["ip"]
        if mac in hosts_dict:
            hosts_dict[mac]["ip"] = ip
            hosts_dict[mac]["status"] = "active"  # ← только здесь ставим active
            hosts_dict[mac]["source"].append("arp")

    # 3. DHCP — обогащение (НЕ влияет на status!)
    for lease in dhcp_leases:
        mac = lease.get("mac")
        if not mac or mac not in hosts_dict:
            continue

        host = hosts_dict[mac]

        # IP из DHCP (fallback, если ARP не дал)
        if host["ip"] == "unknown":
            host["ip"] = lease.get("ip") or host["ip"]

        # DHCP-сервер
        host["dhcp_server"] = lease.get("dhcp_server")

        # Type
        source = lease.get("source")
        if source == "lease":
            host["type"] = "lease"
        elif source == "reservation":
            host["type"] = "reserved"

        # Имя и описание
        host["hostname"] = lease.get("hostname") or lease.get("name") or host["hostname"]
        host["description"] = lease.get("description") or host["description"]

        # Lease end только для lease
        if source == "lease":
            host["lease_end"] = lease.get("lease_end")
        else:
            host["lease_end"] = None

        host["source"].append(source)

    # Fallback для type
    for data in hosts_dict.values():
        if data["type"] == "unknown" and "arp" in data["source"]:
            data["type"] = "static"

        # Если ip есть (ARP дал), но status всё ещё unknown — active
        if data["ip"] != "unknown" and data["status"] == "unknown":
            data["status"] = "active"

    # Валидация
    valid_hosts = []
    for data in hosts_dict.values():
        try:
            host = Host(**data)
            valid_hosts.append(host.model_dump())
        except ValidationError as e:
            print(f"Ошибка валидации хоста {data.get('mac')}: {e}")

    print(f"Сформировано валидных хостов: {len(valid_hosts)}")
    return valid_hosts