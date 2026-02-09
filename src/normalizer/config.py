from typing import Dict, Any, List
from .base import BaseNormalizer

class ConfigNormalizer(BaseNormalizer):
    @classmethod
    def normalize(cls, parsed_data: Dict[str, Any], vendor: str) -> Dict[str, Any]:
        """
        Нормализация конфигурации интерфейсов из show running-config.
        Обрабатываем только поля, которые отсутствуют в show interface brief:
        mode, allowed_vlans, untagged_vlans, pvid, voice_vlan_mode, voice_vlan_vid.
        """
        if "interfaces_config" not in parsed_data:
            return {}

        normalized_interfaces = []

        for raw_intf in parsed_data["interfaces_config"]:
            name = raw_intf["name"].lower()

            # Унификация имени порта (GigaEthernet → g0, TGigaEthernet → tg0)
            if "gigaethernet" in name:
                name = name.replace("gigaethernet", "g")
            elif "tgigaethernet" in name:
                name = name.replace("tgigaethernet", "tg")

            normalized = {
                "name": name,
                "mode": raw_intf["mode"] or "access",
                "allowed_vlans": raw_intf["allowed_vlans"],
                "untagged_vlans": raw_intf["untagged_vlans"],
                "pvid": raw_intf["pvid"] if raw_intf["pvid"] else ("1" if raw_intf["mode"] == "trunk" else None),
                "voice_vlan_mode": raw_intf["voice_vlan_mode"],
                "voice_vlan_vid": raw_intf["voice_vlan_vid"]
            }

            normalized_interfaces.append(normalized)

        return {"interfaces_config_normalized": normalized_interfaces}