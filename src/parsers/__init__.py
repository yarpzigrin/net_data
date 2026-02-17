# src/parsers/__init__.py
from .registry import register_parser, get_parser

# Принудительно импортируем все модули-парсеры при импорте пакета
import src.parsers.nateks
import src.parsers.rvi
# import src.parsers.eltex  # и т.д.