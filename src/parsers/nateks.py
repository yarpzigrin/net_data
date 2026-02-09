import re
from typing import Dict, List, Any
from .base_parser import BaseParser
from .registry import register_parser

class NateksVlanParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        if command != "show vlan":
            return {}

        vlans: List[Dict[str, Any]] = []
        current_vlan = None

        for line in raw_text.splitlines():
            line = line.rstrip()  # убираем trailing spaces

            # Пропускаем заголовки и разделители
            if not line or "----" in line or line.startswith("VLAN Status Name"):
                continue

            # Новая VLAN строка: 1 Static Default g0/4, g0/9, ...
            match_new_vlan = re.match(r"^(\d+)\s+Static\s+([^\s].*?)\s+(.+)$", line)
            if match_new_vlan:
                vlan_id = int(match_new_vlan.group(1))
                name = match_new_vlan.group(2).strip()
                ports_str = match_new_vlan.group(3).strip()

                current_vlan = {
                    "vlan_id": vlan_id,
                    "name": name,
                    "status": "static",
                    "ports": []
                }
                vlans.append(current_vlan)

                # Парсим порты из этой строки
                ports = [p.strip() for p in ports_str.split(",") if p.strip()]
                current_vlan["ports"].extend(ports)
                continue

            # Продолжение портов на следующей строке (отступ + порты)
            if current_vlan and line and line[0].isspace():
                ports = [p.strip() for p in line.split(",") if p.strip()]
                current_vlan["ports"].extend(ports)

        return {"vlans": vlans}


class NateksInterfaceBriefParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        if command != "show interface brief":
            return {}

        interfaces: List[Dict[str, Any]] = []
        current_desc = None

        for line in raw_text.splitlines():
            line = line.rstrip()

            # Пропускаем заголовок
            if not line or "Port Description Status Vlan Duplex Speed Type" in line:
                continue

            # Основная строка: g0/1 shutdown 610 auto auto Giga-TX
            match = re.match(r"^([tg]?[a-z0-9]+/[0-9]+(?:/[0-9]+)?)\s+(.+?)\s+(\w+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$", line)
            if match:
                name, desc, status, vlan, duplex, speed, type_ = match.groups()

                # Если описание "-" — значит оно на следующей строке
                if desc.strip() == "-":
                    current_desc = None
                else:
                    current_desc = desc.strip()

                interfaces.append({
                    "name": name.strip(),
                    "description": current_desc,
                    "status": status.lower(),
                    "vlan": vlan if vlan != "Trunk(1)" else "trunk",
                    "duplex": duplex.lower(),
                    "speed": speed,
                    "type": type_.strip()
                })
                continue

            # Продолжение описания (отступ + текст)
            if current_desc is None and line.strip() and line[0].isspace():
                if interfaces:
                    prev_desc = interfaces[-1]["description"] or ""
                    interfaces[-1]["description"] = (prev_desc + " " + line.strip()).strip()

        return {"interfaces": interfaces}

class NateksVersionParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        if command != "show version":
            return {}

        version_info = {}

        lines = raw_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Модель и версия
            if "NetXpert" in line and "Version" in line:
                parts = line.split("Version")
                if len(parts) > 1:
                    version_info["model"] = parts[0].strip()
                    rest = parts[1].strip()
                    firmware_match = re.search(r"(\S+)\s+Build", rest)
                    if firmware_match:
                        version_info["firmware"] = firmware_match.group(1)
                    build_match = re.search(r"Build\s+(\d+)", rest)
                    if build_match:
                        version_info["build"] = build_match.group(1)

            # Serial num и ID num — в одной строке
            if "Serial num:" in line:
                parts = line.split("Serial num:", 1)
                if len(parts) > 1:
                    rest = parts[1].strip()
                    if ", ID num:" in rest:
                        serial_part, id_part = rest.split(", ID num:", 1)
                        version_info["serial_number"] = serial_part.strip()
                        version_info["id_number"] = id_part.strip()
                    else:
                        version_info["serial_number"] = rest.strip()

            # vend_ID и product_ID
            if "vend_ID:" in line:
                version_info["vend_ID"] = line.split("vend_ID:")[1].split()[0].strip()
            if "product_ID:" in line:
                version_info["product_ID"] = line.split("product_ID:")[1].split()[0].strip()

        return {"version_info": version_info}

class NateksIpInterfaceParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        if command != "show ip interface brief":
            return {}

        svis = []

        for line in raw_text.splitlines():
            line = line.strip()
            if not line or "Interface IP-Address Method Protocol-Status" in line:
                continue

            # VLAN1 unassigned manual down
            # VLAN610 10.66.10.1 manual up
            match = re.match(r"^(VLAN\d+)\s+(\S+)\s+(\S+)\s+(\S+)$", line)
            if match:
                interface, ip_addr, method, status = match.groups()
                svis.append({
                    "interface": interface,
                    "ip_address": ip_addr if ip_addr != "unassigned" else None,
                    "status": status.lower()
                })

        return {"svi": svis}

class NateksRunningConfigParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        if command != "show running-config":
            return {}

        interfaces = []

        lines = raw_text.splitlines()
        current_data = None

        for line in lines:
            line = line.rstrip()

            if not line or line.startswith("!"):
                continue

            # Новая интерфейсная команда — завершаем предыдущую и начинаем новую
            if line.startswith("interface "):
                if current_data:
                    interfaces.append(current_data)
                current_data = {
                    "name": line.split("interface ", 1)[1].strip(),
                    "mode": "access",
                    "allowed_vlans": None,
                    "untagged_vlans": None,
                    "pvid": None,
                    "voice_vlan_mode": None,
                    "voice_vlan_vid": None
                }
                continue

            # Если мы внутри интерфейса — парсим параметры
            if current_data:
                if "switchport mode trunk" in line:
                    current_data["mode"] = "trunk"
                if "switchport trunk vlan-allowed" in line:
                    current_data["allowed_vlans"] = line.split("vlan-allowed", 1)[1].strip()
                if "switchport trunk vlan-untagged" in line:
                    current_data["untagged_vlans"] = line.split("vlan-untagged", 1)[1].strip()
                if "switchport pvid" in line:
                    current_data["pvid"] = line.split("switchport pvid", 1)[1].strip()
                if "switchport voice-vlan mode" in line:
                    current_data["voice_vlan_mode"] = line.split("switchport voice-vlan mode", 1)[1].strip()
                if "switchport voice-vlan " in line and "mode" not in line:
                    current_data["voice_vlan_vid"] = line.split("switchport voice-vlan", 1)[1].strip()

        # Не забываем добавить последний интерфейс
        if current_data:
            interfaces.append(current_data)

        return {"interfaces_config": interfaces}

class NateksMacAddressTableParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str, device_ip: str = None, device_hostname: str = None) -> Dict[str, Any]:
        if command != "show mac address-table":
            return {}

        entries = []

        lines = raw_text.splitlines()
        parsing = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "Mac Address Table" in line or "Vlan" in line and "Mac Address" in line:
                parsing = True
                continue

            if parsing and line:
                parts = line.split()
                if len(parts) >= 4:
                    vlan = parts[0]
                    mac_raw = parts[1]
                    mac_type = parts[2]
                    port = parts[3]

                    # Нормализация MAC → 12 символов без разделителей
                    mac_clean = mac_raw.replace(".", "").replace(":", "").lower()
                    if len(mac_clean) != 12 or not all(c in "0123456789abcdef" for c in mac_clean):
                        continue

                    entry = {
                        "vlan": vlan,
                        "mac": mac_clean,
                        "type": mac_type,
                        "port": port
                    }

                    if device_ip:
                        entry["device_ip"] = device_ip
                    if device_hostname:
                        entry["device_hostname"] = device_hostname

                    entries.append(entry)

        print(f"[DEBUG] Спарсено MAC-записей: {len(entries)}")
        return {"mac_entries": entries}

class NateksArpParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        if command != "show arp":
            return {}

        entries = []

        lines = raw_text.splitlines()
        parsing = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "Total ARP entries" in line or "Protocol Address" in line:
                parsing = True
                continue

            if parsing and line and "IP " in line:
                parts = line.split()
                if len(parts) < 5 or parts[0] != "IP":
                    continue

                ip = parts[1]
                age = parts[2] if parts[2] != "-" else None
                mac_raw = parts[3]
                mac_type = parts[4]
                interface = " ".join(parts[5:]) if len(parts) > 5 else None

                mac_clean = mac_raw.replace(":", "").replace(".", "").lower()
                if len(mac_clean) != 12 or not all(c in "0123456789abcdef" for c in mac_clean):
                    continue

                entry = {
                    "ip": ip,
                    "mac": mac_clean,
                    "age": age,
                    "type": mac_type,
                    "interface": interface
                }

                entries.append(entry)

        print(f"[DEBUG] Спарсено ARP-записей: {len(entries)}")
        return {"arp_entries": entries}


# Регистрация
register_parser("nateks", "vlan", NateksVlanParser.parse)
register_parser("nateks", "interface_brief", NateksInterfaceBriefParser.parse)
register_parser("nateks", "version", NateksVersionParser.parse)
register_parser("nateks", "ip_interface", NateksIpInterfaceParser.parse)
register_parser("nateks", "running_config", NateksRunningConfigParser.parse)
register_parser("nateks", "mac_address_table", NateksMacAddressTableParser.parse)
register_parser("nateks", "arp", NateksArpParser.parse)
