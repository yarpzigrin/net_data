from typing import Dict, Any
from src.normalizer.base_normalizer import BaseNormalizer

class VersionNormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        if "version_info" not in parsed_data:
            return {}

        info = parsed_data["version_info"]
        normalized = {}

        # Берём только те поля, которые есть и не пустые
        for key in ["model", "firmware", "build", "serial_number", "vend_ID", "product_ID", "ID"]:
            value = info.get(key)
            if value and value.strip():
                normalized[key] = value.strip()

        return normalized