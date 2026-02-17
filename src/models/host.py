from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class Host(BaseModel):
    mac: str = Field(..., pattern=r'^[0-9a-f]{12}$')
    ip: str = "unknown"
    status: str = "unknown"  # active / unknown / reserved(active) / reserved(inactive)
    type: str = "unknown"    # lease / reserved / static / unknown
    vlan: Optional[str] = None
    port: Optional[str] = None
    device_ip: str
    device_hostname: str
    description: Optional[str] = None
    hostname: Optional[str] = None
    dhcp_server: Optional[str] = None
    lease_end: Optional[str] = None
    source: List[str] = Field(default_factory=list)