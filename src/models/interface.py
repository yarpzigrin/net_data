from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

class Interface(BaseModel):
    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    status: Literal["up", "down", "shutdown", "notconnect", "err-disabled"] = "down"
    vlan: str
    duplex: Literal["full", "half", "auto", "unknown"] = "auto"
    speed: str | int = Field("auto")  # ← теперь может быть строкой ("auto") или числом (100, 1000)
    type: str

    # Новые поля из running-config
    mode: Literal["access", "trunk"] = "access"
    allowed_vlans: Optional[str] = None
    untagged_vlans: Optional[str] = None
    pvid: str = "1"
    voice_vlan_mode: Optional[str] = None
    voice_vlan_vid: Optional[str] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.lower().replace(" ", "")

    class Config:
        json_encoders = {}