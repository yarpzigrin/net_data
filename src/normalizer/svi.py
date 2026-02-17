from typing import Dict, Any, List
from src.normalizer.base_normalizer import BaseNormalizer
from src.models.svi import SVI

class SVINormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        if "svi" not in parsed_data:
            return {}

        normalized = []
        for raw_svi in parsed_data["svi"]:
            norm = {
                "interface": raw_svi["interface"],
                "ip_address": raw_svi["ip_address"],
                "status": raw_svi["status"].lower(),
                "description": None  # заполним позже
            }
            try:
                validated = SVI(**norm)
                normalized.append(validated.model_dump())
            except Exception as e:
                print(f"Ошибка валидации SVI {norm['interface']}: {e}")
                continue

        return {"svi": normalized}