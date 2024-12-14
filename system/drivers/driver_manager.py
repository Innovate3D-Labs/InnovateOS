#!/usr/bin/env python3
import os
import json
import importlib
import logging
import subprocess
from typing import Dict, List, Optional
from pathlib import Path

class DriverManager:
    def __init__(self):
        self.driver_dir = Path("/usr/lib/innovate/drivers")
        self.config_dir = Path("/etc/innovate/drivers")
        self.logger = self._setup_logging()
        self.loaded_drivers: Dict[str, object] = {}
        
        # Erstelle Verzeichnisse
        self.driver_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logging(self):
        logger = logging.getLogger('DriverManager')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('/var/log/innovate_drivers.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger
        
    def _load_driver_config(self, driver_name: str) -> Dict:
        """Lädt die Treiberkonfiguration"""
        config_file = self.config_dir / f"{driver_name}.json"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def _save_driver_config(self, driver_name: str, config: Dict):
        """Speichert die Treiberkonfiguration"""
        config_file = self.config_dir / f"{driver_name}.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    def install_driver(self, driver_package: str) -> bool:
        """Installiert einen neuen Treiber"""
        try:
            # Extrahiere Treiber-Paket
            if os.path.isfile(driver_package):
                subprocess.run(["tar", "xzf", driver_package, "-C", str(self.driver_dir)],
                             check=True)
            else:
                # Versuche Treiber aus Repository zu installieren
                subprocess.run(["pip", "install", "-t", str(self.driver_dir), driver_package],
                             check=True)
                             
            self.logger.info(f"Treiber installiert: {driver_package}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Treiberinstallation: {e}")
            return False
            
    def load_driver(self, driver_name: str) -> Optional[object]:
        """Lädt einen Treiber"""
        if driver_name in self.loaded_drivers:
            return self.loaded_drivers[driver_name]
            
        try:
            # Füge Treiber-Verzeichnis zum Python-Pfad hinzu
            import sys
            if str(self.driver_dir) not in sys.path:
                sys.path.append(str(self.driver_dir))
                
            # Importiere Treiber-Modul
            module = importlib.import_module(f"{driver_name}_driver")
            driver = module.Driver()  # Annahme: Jeder Treiber hat eine Driver-Klasse
            
            # Lade Konfiguration
            config = self._load_driver_config(driver_name)
            driver.configure(config)
            
            self.loaded_drivers[driver_name] = driver
            self.logger.info(f"Treiber geladen: {driver_name}")
            return driver
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Treibers {driver_name}: {e}")
            return None
            
    def unload_driver(self, driver_name: str) -> bool:
        """Entlädt einen Treiber"""
        try:
            if driver_name in self.loaded_drivers:
                driver = self.loaded_drivers[driver_name]
                driver.cleanup()  # Annahme: Treiber haben eine cleanup-Methode
                del self.loaded_drivers[driver_name]
                self.logger.info(f"Treiber entladen: {driver_name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Entladen des Treibers {driver_name}: {e}")
            return False
            
    def configure_driver(self, driver_name: str, config: Dict) -> bool:
        """Konfiguriert einen Treiber"""
        try:
            if driver_name in self.loaded_drivers:
                driver = self.loaded_drivers[driver_name]
                driver.configure(config)
                self._save_driver_config(driver_name, config)
                self.logger.info(f"Treiber konfiguriert: {driver_name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler bei Treiberkonfiguration {driver_name}: {e}")
            return False
            
    def list_available_drivers(self) -> List[Dict]:
        """Listet verfügbare Treiber auf"""
        drivers = []
        for path in self.driver_dir.glob("*_driver.py"):
            driver_name = path.stem.replace("_driver", "")
            config = self._load_driver_config(driver_name)
            drivers.append({
                'name': driver_name,
                'loaded': driver_name in self.loaded_drivers,
                'config': config
            })
        return drivers
        
    def get_driver_info(self, driver_name: str) -> Optional[Dict]:
        """Holt detaillierte Informationen zu einem Treiber"""
        try:
            if driver_name in self.loaded_drivers:
                driver = self.loaded_drivers[driver_name]
                return {
                    'name': driver_name,
                    'version': getattr(driver, 'version', 'unknown'),
                    'status': 'loaded',
                    'capabilities': getattr(driver, 'capabilities', []),
                    'config': self._load_driver_config(driver_name)
                }
                
            driver_path = self.driver_dir / f"{driver_name}_driver.py"
            if driver_path.exists():
                # Lade Treiber temporär für Info
                module = importlib.import_module(f"{driver_name}_driver")
                return {
                    'name': driver_name,
                    'version': getattr(module, 'VERSION', 'unknown'),
                    'status': 'available',
                    'capabilities': getattr(module, 'CAPABILITIES', []),
                    'config': self._load_driver_config(driver_name)
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Treiberinfo {driver_name}: {e}")
            return None
            
    def update_driver(self, driver_name: str, driver_package: str) -> bool:
        """Aktualisiert einen Treiber"""
        try:
            # Entlade alten Treiber
            self.unload_driver(driver_name)
            
            # Sichere alte Konfiguration
            old_config = self._load_driver_config(driver_name)
            
            # Entferne alte Treiberdateien
            old_files = self.driver_dir.glob(f"{driver_name}_driver*")
            for file in old_files:
                file.unlink()
                
            # Installiere neue Version
            if self.install_driver(driver_package):
                # Lade Treiber mit alter Konfiguration
                driver = self.load_driver(driver_name)
                if driver:
                    self.configure_driver(driver_name, old_config)
                    self.logger.info(f"Treiber aktualisiert: {driver_name}")
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Update des Treibers {driver_name}: {e}")
            return False
            
    def auto_detect_hardware(self) -> List[Dict]:
        """Erkennt automatisch angeschlossene Hardware"""
        detected = []
        
        # USB-Geräte erkennen
        try:
            import usb.core
            devices = usb.core.find(find_all=True)
            for device in devices:
                detected.append({
                    'type': 'usb',
                    'vendor_id': device.idVendor,
                    'product_id': device.idProduct,
                    'manufacturer': device.manufacturer,
                    'product': device.product
                })
        except ImportError:
            self.logger.warning("pyusb nicht installiert")
            
        # Serielle Ports scannen
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                detected.append({
                    'type': 'serial',
                    'port': port.device,
                    'description': port.description,
                    'manufacturer': port.manufacturer,
                    'hardware_id': port.hwid
                })
        except ImportError:
            self.logger.warning("pyserial nicht installiert")
            
        return detected
        
if __name__ == "__main__":
    manager = DriverManager()
    print("Verfügbare Treiber:", manager.list_available_drivers())
    print("Erkannte Hardware:", manager.auto_detect_hardware())
