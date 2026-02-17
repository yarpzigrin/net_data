from typing import Dict, Any
from src.normalizer.base_normalizer import BaseNormalizer

class ArpNormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        entries = parsed_data.get("arp_entries", [])
        normalized = []

        for entry in entries:
            normalized.append({
                "ip": entry["ip"],
                "mac": entry["mac"],
                "age": entry["age"],
                "interface": entry["interface"]
            })

        return {"arp_entries_normalized": normalized}