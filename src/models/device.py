from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class Device(BaseModel):
    ip: str
    hostname: str
    vendor: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware: Optional[str] = None
    build: Optional[str] = None
    vend_ID: Optional[str] = None
    product_ID: Optional[str] = None
    ID: Optional[str] = None
    location: str = "unknown"
    status: str = "reachable"
    vlans: List[Dict] = Field(default_factory=list)
    interfaces: List[Dict] = Field(default_factory=list)
    lldp_neighbors: List[Dict] = Field(default_factory=list)
    svi: List[Dict] = Field(default_factory=list)
    static_config: Dict = Field(default_factory=dict)

    class Config:
        json_encoders = {}