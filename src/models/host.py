from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class Host(BaseModel):
    mac: str = Field(..., pattern=r'^[0-9a-f]{12}$')
    ip: Optional[str] = Field(None, description="IP из ARP или DHCP, 'unknown' если нет")
    vlan: str
    port: str
    device_ip: str
    device_hostname: str
    description: Optional[str] = None
    type: Literal["lease", "reserved", "static", "unknown"] = "unknown"
    status: Literal["active", "inactive", "reserved(inactive)", "unknown"] = "unknown"
    source: List[str] = Field(default_factory=list)