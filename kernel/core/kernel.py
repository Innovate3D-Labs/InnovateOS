import os
import sys
import logging
from typing import Dict, Optional

class InnovateKernel:
    def __init__(self):
        self.devices: Dict[str, 'PrinterDevice'] = {}
        self.scheduler = PrintScheduler()
        self.hal = HardwareAbstractionLayer()
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        logger = logging.getLogger('InnovateOS')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger
        
    def register_device(self, device: 'PrinterDevice'):
        """Registriert einen neuen Drucker im System"""
        self.devices[device.id] = device
        self.logger.info(f"Neuer Drucker registriert: {device.id}")
        
    def get_device(self, device_id: str) -> Optional['PrinterDevice']:
        """Gibt ein Drucker-Objekt zurück"""
        return self.devices.get(device_id)
        
    def schedule_print(self, device_id: str, gcode_file: str):
        """Plant einen Druckauftrag ein"""
        device = self.get_device(device_id)
        if not device:
            raise ValueError(f"Drucker {device_id} nicht gefunden")
        
        self.scheduler.add_job(device, gcode_file)
        
    def start(self):
        """Startet den Kernel"""
        self.logger.info("InnovateOS Kernel wird gestartet...")
        self.hal.initialize()
        self.scheduler.start()
        
    def shutdown(self):
        """Fährt den Kernel sicher herunter"""
        self.logger.info("InnovateOS wird heruntergefahren...")
        for device in self.devices.values():
            device.safe_shutdown()
        self.scheduler.stop()
        self.hal.cleanup()
