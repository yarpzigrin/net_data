import re
from typing import Dict, Any, List
from src.parsers.base_parser import BaseParser
from src.parsers.registry import register_parser

class DhcpLeasesParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str = None) -> Dict[str, Any]:
        if "dhcp_leases" not in command.lower():
            return {}

        entries: List[Dict] = []
        current_entry = {}

        lines = raw_text.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry and current_entry.get("mac"):
                    entries.append(current_entry)
                current_entry = {}
                continue

            if " : " in line:
                key, value = [x.strip() for x in line.split(" : ", 1)]
                if key == "IPAddress":
                    current_entry["ip"] = value
                elif key == "ClientId":
                    mac_clean = value.replace("-", "").replace(":", "").replace(".", "").lower()
                    if len(mac_clean) == 12:
                        current_entry["mac"] = mac_clean
                elif key == "HostName":
                    current_entry["hostname"] = value if value else None
                elif key == "AddressState":
                    current_entry["address_state"] = value
                elif key == "LeaseExpiryTime":
                    current_entry["lease_end"] = value if value else None

        # Не забудем последнюю запись
        if current_entry and current_entry.get("mac"):
            entries.append(current_entry)

        print(f"[DHCP PARSER] Спарсено leases: {len(entries)}")
        return {"dhcp_leases": entries}


class DhcpReservationsParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str = None) -> Dict[str, Any]:
        if "dhcp_reservations" not in command.lower():
            return {}

        entries: List[Dict] = []
        current_entry = {}

        lines = raw_text.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry and current_entry.get("mac"):
                    entries.append(current_entry)
                current_entry = {}
                continue

            if " : " in line:
                key, value = [x.strip() for x in line.split(" : ", 1)]
                if key == "IPAddress":
                    current_entry["ip"] = value
                elif key == "ClientId":
                    mac_clean = value.replace("-", "").replace(":", "").replace(".", "").lower()
                    if len(mac_clean) == 12:
                        current_entry["mac"] = mac_clean
                elif key == "Name":
                    current_entry["name"] = value if value else None
                elif key == "Description":
                    current_entry["description"] = value if value else None
                elif key == "Type":
                    current_entry["type"] = value

        if current_entry and current_entry.get("mac"):
            entries.append(current_entry)

        print(f"[DHCP PARSER] Спарсено reservations: {len(entries)}")
        return {"dhcp_reservations": entries}


# Регистрация — теперь отдельно от вендора
register_parser("dhcp", "dhcp_leases", DhcpLeasesParser.parse)
register_parser("dhcp", "dhcp_reservations", DhcpReservationsParser.parse)