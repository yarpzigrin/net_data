import re
from typing import Dict, Any
from src.parsers.base_parser import BaseParser
from src.parsers.registry import register_parser
from src.filters.port_filters import is_ignored_port

class RViMacAddressTableParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str, device_ip: str = None, device_hostname: str = None) -> Dict[str, Any]:
        if command != "show mac address-table":
            return {}

        entries = []

        lines = raw_text.splitlines()
        parsing = False

        for line in lines:
            # Не strip'им сразу — чтобы не потерять начало строки
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # Ищем начало таблицы (гибко — содержит ключевые слова)
            if "bridge" in line_stripped and "VLAN" in line_stripped and "port" in line_stripped and "mac" in line_stripped:
                parsing = True
                continue

            if parsing and line_stripped:
                # Разбиваем по любым пробелам (RVi использует несколько)
                parts = re.split(r'\s+', line_stripped)
                if len(parts) >= 6:
                    # Структура: bridge VLAN port mac fwd static
                    # Пример: 1 1 xe1/52 40f4.1347.8652 1 0
                    vlan = parts[1]
                    port = parts[2]
                    mac_raw = parts[3]

                    # Нормализация MAC
                    mac_clean = mac_raw.replace(".", "").lower()
                    if len(mac_clean) != 12 or not all(c in "0123456789abcdef" for c in mac_clean):
                        continue

                    # Фильтрация портов
                    if device_ip and is_ignored_port(device_ip, port):
                        continue

                    entry = {
                        "vlan": vlan,
                        "mac": mac_clean,
                        "type": "dynamic",  # RVi не указывает явно
                        "port": port,
                    }

                    if device_ip:
                        entry["device_ip"] = device_ip
                    if device_hostname:
                        entry["device_hostname"] = device_hostname

                    entries.append(entry)

        print(f"[DEBUG] Спарсено MAC-записей RVi: {len(entries)}")
        return {"mac_entries": entries}


# Регистрация (должна быть в конце файла)
register_parser("rvi", "mac_address_table", RViMacAddressTableParser.parse)