from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class Host(BaseModel):
    mac: str = Field(..., pattern=r'^[0-9a-f]{12}$')  # строго 12 hex-символов, нижний регистр
    ip: Optional[str] = None
    vlan: str
    port: Optional[str] = None
    device_ip: str
    device_hostname: str
    description: Optional[str] = None
    type: Literal["lease", "reserved"] = "lease"
    status: Literal["active", "inactive", "reserved(inactive)"] = "active"