from typing import Dict, Any

class BaseParser:
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        raise NotImplementedError("Реализуйте метод parse в наследнике")