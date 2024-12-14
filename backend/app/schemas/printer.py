from pydantic import BaseModel
from typing import Optional, Dict

class PrinterBase(BaseModel):
    name: str
    model: str
    firmware: str
    connection_type: str
    ip_address: Optional[str] = None
    port: Optional[int] = None
    status: str = "Idle"
    temperature: Dict[str, float] = {"bed": 0.0, "extruder": 0.0}
    settings: Dict = {}

class PrinterCreate(PrinterBase):
    pass

class Printer(PrinterBase):
    id: int

    class Config:
        orm_mode = True
