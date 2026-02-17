from typing import Dict, Any
from src.normalizer.base_normalizer import BaseNormalizer

class MacTableNormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        entries = parsed_data.get("mac_entries", [])
        normalized = []

        for entry in entries:
            normalized.append({
                "vlan": entry["vlan"],
                "mac": entry["mac"],
                "type": entry["type"],
                "port": entry["port"],
                "device_ip": entry.get("device_ip"),
                "device_hostname": entry.get("device_hostname")
            })

        return {"mac_entries_normalized": normalized}