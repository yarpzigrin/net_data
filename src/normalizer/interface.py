from typing import Dict, Any, List
from .base import BaseNormalizer
from src.models.interface import Interface

class InterfaceNormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        if "interfaces" not in parsed_data:
            return {}

        normalized = []
        seen_names = set()

        for raw_intf in parsed_data["interfaces"]:
            name = raw_intf["name"].lower()

            if name in seen_names:
                print(f"Дедуп интерфейс {name}")
                continue
            seen_names.add(name)

            # Унификация speed
            speed_str = raw_intf.get("speed", "auto")
            if speed_str == "auto":
                speed_normalized = "auto"
            elif "Mb" in speed_str:
                cleaned = speed_str.replace("Mb", "").replace(" ", "").strip()
                try:
                    speed_normalized = int(cleaned)
                except ValueError:
                    speed_normalized = speed_str  # fallback
            else:
                speed_normalized = speed_str

            normalized_intf = {
                "name": name,
                "description": (raw_intf.get("description") or "").strip() or None,
                "status": raw_intf.get("status", "down").lower(),
                "vlan": raw_intf.get("vlan", "1"),
                "duplex": raw_intf.get("duplex", "auto").lower(),
                "speed": speed_normalized,
                "type": raw_intf.get("type", "unknown")
            }

            try:
                validated = Interface(**normalized_intf)
                normalized.append(validated.model_dump())
            except Exception as e:
                print(f"Ошибка валидации интерфейса {name}: {e}")
                continue

        return {"interfaces": normalized}