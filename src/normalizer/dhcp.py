from typing import Dict, Any, List

class DhcpNormalizer:
    @classmethod
    def normalize_leases(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        entries = parsed_data.get("dhcp_leases", [])
        normalized = []

        for entry in entries:
            normalized.append({
                "ip": entry.get("ip"),
                "mac": entry.get("mac"),
                "hostname": entry.get("hostname"),
                "address_state": entry.get("address_state"),
                "lease_end": entry.get("lease_end"),
                "dhcp_server": entry.get("dhcp_server"),  # ← сохраняем
                "source": "lease"
            })

        return {"dhcp_leases_normalized": normalized}

    @classmethod
    def normalize_reservations(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        entries = parsed_data.get("dhcp_reservations", [])
        normalized = []

        for entry in entries:
            normalized.append({
                "ip": entry.get("ip"),
                "mac": entry.get("mac"),
                "name": entry.get("name"),
                "description": entry.get("description"),
                "type": entry.get("type"),
                "dhcp_server": entry.get("dhcp_server"),  # ← сохраняем
                "source": "reservation"
            })

        return {"dhcp_reservations_normalized": normalized}