from pydantic import BaseModel, Field
from typing import Optional

class DhcpEntry(BaseModel):
    ip: str
    mac: str = Field(..., pattern=r'^[0-9a-f]{12}$')  # чистим до 12 hex
    hostname: Optional[str] = None  # из HostName или Name
    description: Optional[str] = None  # из Description, если есть
    type: str = "lease"  # lease / reserved
    status: str = "unknown"  # active / inactive / reserved(active) / reserved(inactive)
    lease_end: Optional[str] = None  # ISO или пусто
    source: str = "dhcp"  # откуда пришла запись