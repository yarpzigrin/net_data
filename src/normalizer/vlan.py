from typing import Dict, Any, List
from .base import BaseNormalizer
from src.models.vlan import Vlan

class VlanNormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        if "vlans" not in parsed_data:
            return {}

        normalized_vlans = []
        seen_ids = set()  # для дедупликации

        for raw_vlan in parsed_data["vlans"]:
            vlan_id = raw_vlan["vlan_id"]

            if vlan_id in seen_ids:
                print(f"Дедуп VLAN {vlan_id} — уже обработан")
                continue
            seen_ids.add(vlan_id)

            # Унификация
            normalized = {
                "vlan_id": int(vlan_id),
                "name": raw_vlan["name"].strip(),
                "status": raw_vlan["status"].lower(),
                "ports": sorted(raw_vlan["ports"])  # уже list[str]
            }

            # Валидация через Pydantic
            try:
                validated = Vlan(**normalized)
                normalized_vlans.append(validated.model_dump())
            except Exception as e:
                print(f"Ошибка валидации VLAN {vlan_id}: {e}")
                continue

        return {"vlans": normalized_vlans}