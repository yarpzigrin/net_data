import re
from typing import Dict, List, Any
from .base_parser import BaseParser
from .registry import register_parser

class RviVlanParser(BaseParser):
    @classmethod
    def parse(cls, command: str, raw_text: str, vendor: str) -> Dict[str, Any]:
        if command != "show vlan":
            return {}

        vlans: List[Dict[str, Any]] = []
        lines = raw_text.splitlines()

        # Пропускаем заголовок
        i = 0
        while i < len(lines) and not lines[i].strip().startswith("----"):
            i += 1
        i += 1  # пропускаем строку ----

        for line in lines[i:]:
            line = line.strip()
            if not line:
                continue

            # Пример: 1 vlan1 active [S] [u]xe1/49 [u]xe1/50 ...
            match = re.match(r"^(\d+)\s+([^\s]+)\s+(\w+)\s+$$   S   $$\s+(.*)$", line)
            if match:
                vlan_id = int(match.group(1))
                name = match.group(2)
                status = match.group(3).lower()
                ports_str = match.group(4)

                ports = []
                for port_part in re.findall(r"$$   ([ut])   $$([^ \[]+)", ports_str):
                    tag, port = port_part
                    ports.append({"port": port.strip(), "tag": "untagged" if tag == "u" else "tagged"})

                vlans.append({
                    "vlan_id": vlan_id,
                    "name": name,
                    "status": status,
                    "ports": ports
                })

        return {"vlans": vlans}

register_parser("rvi", "vlan", RviVlanParser.parse)