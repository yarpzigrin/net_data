from typing import List
from pydantic import BaseModel, field_validator, Field
import re

class VlanPort(BaseModel):
    port: str

class Vlan(BaseModel):
    vlan_id: int = Field(..., ge=1, le=4094)
    name: str = Field(..., min_length=1)
    status: str = Field(..., pattern=r"^(static|active|suspended)$")
    ports: List[str] = Field(default_factory=list)

    @field_validator("ports")
    @classmethod
    def sort_and_unique_ports(cls, v: List[str]) -> List[str]:
        def port_key(port: str) -> tuple:
            # Разбиваем на префикс (g0/, tg0/, ge1/) и номер
            match = re.match(r"([a-z]+[0-9]*/?)([0-9]+(?:/[0-9]+)?)", port.lower())
            if match:
                prefix, number = match.groups()
                # Разбиваем номер на части (например 1/0/5 → (1,0,5))
                num_parts = tuple(int(x) for x in number.split('/'))
                return (prefix, num_parts)
            return (port.lower(), ())  # fallback для нестандартных имён

        unique_ports = set(v)  # убираем дубликаты
        sorted_ports = sorted(unique_ports, key=port_key)
        return sorted_ports

    class Config:
        json_encoders = {}