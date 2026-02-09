from typing import Optional
from pydantic import BaseModel, Field

class SVI(BaseModel):
    interface: str = Field(..., pattern=r"^VLAN\d+$")
    ip_address: Optional[str] = None
    status: str = Field(..., pattern=r"^(up|down)$")
    description: Optional[str] = None  # заполним позже из vlans

    class Config:
        json_encoders = {}