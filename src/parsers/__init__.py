# src/parsers/__init__.py
from .registry import register_parser, get_parser
from .nateks import NateksVlanParser  # ← это заставит выполнить register_parser внутри nateks.py
from .rvi import RviVlanParser        # если есть
from src.normalizer.vlan import VlanNormalizer
# Регистрация нормализатора (можно в отдельном registry_normalizer.py позже)
# Пока просто импортируем, чтобы знать, что он существует