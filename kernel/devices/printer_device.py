from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import time

class PrinterState(Enum):
    OFFLINE = "offline"
    IDLE = "idle"
    PRINTING = "printing"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class Temperature:
    hotend: float
    bed: float
    target_hotend: float
    target_bed: float

class PrinterDevice:
    def __init__(self, device_id: str, port: str):
        self.id = device_id
        self.port = port
        self.state = PrinterState.OFFLINE
        self.temperature = Temperature(0.0, 0.0, 0.0, 0.0)
        self.position = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0}
        self.current_file: Optional[str] = None
        self.progress: float = 0.0
        
    def connect(self, hal) -> bool:
        """Verbindet den Drucker"""
        try:
            self.connection = hal.connect_printer(self.port)
            if self.connection:
                self.state = PrinterState.IDLE
                return True
            return False
        except Exception as e:
            print(f"Verbindungsfehler: {e}")
            return False
            
    def start_print(self, gcode_file: str) -> bool:
        """Startet einen Druckauftrag"""
        if self.state != PrinterState.IDLE:
            return False
            
        self.current_file = gcode_file
        self.state = PrinterState.PRINTING
        self.progress = 0.0
        return True
        
    def pause_print(self):
        """Pausiert den aktuellen Druck"""
        if self.state == PrinterState.PRINTING:
            self.state = PrinterState.PAUSED
            
    def resume_print(self):
        """Setzt den pausierten Druck fort"""
        if self.state == PrinterState.PAUSED:
            self.state = PrinterState.PRINTING
            
    def cancel_print(self):
        """Bricht den aktuellen Druck ab"""
        if self.state in [PrinterState.PRINTING, PrinterState.PAUSED]:
            self.state = PrinterState.IDLE
            self.current_file = None
            self.progress = 0.0
            
    def update_temperature(self, hotend: float, bed: float):
        """Aktualisiert die Temperaturwerte"""
        self.temperature.hotend = hotend
        self.temperature.bed = bed
        
    def set_temperature(self, hotend: float, bed: float):
        """Setzt neue Zieltemperaturen"""
        self.temperature.target_hotend = hotend
        self.temperature.target_bed = bed
        
    def move(self, x: Optional[float] = None, y: Optional[float] = None, 
            z: Optional[float] = None, e: Optional[float] = None):
        """Bewegt den Druckkopf zu einer Position"""
        if x is not None:
            self.position["X"] = x
        if y is not None:
            self.position["Y"] = y
        if z is not None:
            self.position["Z"] = z
        if e is not None:
            self.position["E"] = e
            
    def home(self):
        """Fährt alle Achsen in die Home-Position"""
        self.position = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0}
        
    def safe_shutdown(self):
        """Fährt den Drucker sicher herunter"""
        if self.state == PrinterState.PRINTING:
            self.pause_print()
        # Kühle Hotend und Bett ab
        self.set_temperature(0, 0)
        # Warte kurz auf Abkühlung
        time.sleep(1)
        self.state = PrinterState.OFFLINE
