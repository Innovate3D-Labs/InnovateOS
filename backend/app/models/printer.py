from sqlalchemy import Column, Integer, String, Float, Boolean, JSON
from ..database import Base

class Printer(Base):
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    model = Column(String)
    firmware = Column(String)
    connection_type = Column(String)  # USB, Network, etc.
    ip_address = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    status = Column(String)  # Idle, Printing, Error
    temperature = Column(JSON)  # {bed: float, extruder: float}
    settings = Column(JSON)  # Printer specific settings
