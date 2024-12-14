#!/usr/bin/env python3
import os
import sys
import signal
import logging
import subprocess
from typing import List, Dict
from pathlib import Path

class InnovateInit:
    """Init-System für InnovateOS"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.services: Dict[str, subprocess.Popen] = {}
        self.running = True
        
    def _setup_logging(self):
        logger = logging.getLogger('InnovateInit')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('/var/log/innovate_init.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger
        
    def _handle_signal(self, signum, frame):
        """Signal-Handler für sauberes Herunterfahren"""
        self.logger.info(f"Signal {signum} empfangen, fahre System herunter...")
        self.running = False
        self.shutdown()
        
    def mount_filesystems(self):
        """Mountet wichtige Filesysteme"""
        filesystems = [
            ("proc", "/proc", "proc"),
            ("sysfs", "/sys", "sysfs"),
            ("devpts", "/dev/pts", "devpts"),
            ("tmpfs", "/run", "tmpfs")
        ]
        for fs_type, mount_point, fs_name in filesystems:
            try:
                if not os.path.ismount(mount_point):
                    os.makedirs(mount_point, exist_ok=True)
                    subprocess.run(["mount", "-t", fs_type, fs_name, mount_point])
                    self.logger.info(f"Mounted {fs_name} auf {mount_point}")
            except Exception as e:
                self.logger.error(f"Fehler beim Mounten von {fs_name}: {e}")
                
    def setup_devices(self):
        """Richtet Gerätedateien ein"""
        devices = [
            ("/dev/null", 0o666),
            ("/dev/zero", 0o666),
            ("/dev/tty", 0o666),
            ("/dev/console", 0o600)
        ]
        for device, mode in devices:
            if not os.path.exists(device):
                os.mknod(device, mode)
                self.logger.info(f"Gerätedatei {device} erstellt")
                
    def start_service(self, name: str, command: List[str]):
        """Startet einen Systemdienst"""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.services[name] = process
            self.logger.info(f"Dienst {name} gestartet (PID: {process.pid})")
        except Exception as e:
            self.logger.error(f"Fehler beim Starten von {name}: {e}")
            
    def start_core_services(self):
        """Startet die Kerndienste"""
        services = {
            "kernel": ["python3", "/usr/local/bin/innovate_kernel"],
            "network": ["python3", "/usr/local/bin/network_manager"],
            "printer_manager": ["python3", "/usr/local/bin/printer_manager"]
        }
        for name, command in services.items():
            self.start_service(name, command)
            
    def monitor_services(self):
        """Überwacht laufende Dienste"""
        while self.running:
            for name, process in list(self.services.items()):
                if process.poll() is not None:
                    self.logger.warning(f"Dienst {name} beendet, starte neu...")
                    self.services.pop(name)
                    self.start_service(name, process.args)
                    
    def shutdown(self):
        """Fährt das System sauber herunter"""
        self.logger.info("Beginne Systemshutdown...")
        
        # Beende alle Dienste
        for name, process in self.services.items():
            self.logger.info(f"Beende Dienst {name}")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                
        # Unmounte Filesysteme
        filesystems = ["/run", "/dev/pts", "/sys", "/proc"]
        for fs in filesystems:
            try:
                if os.path.ismount(fs):
                    subprocess.run(["umount", fs])
                    self.logger.info(f"Unmounted {fs}")
            except Exception as e:
                self.logger.error(f"Fehler beim Unmounten von {fs}: {e}")
                
    def run(self):
        """Hauptmethode des Init-Systems"""
        # Registriere Signal-Handler
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        
        self.logger.info("InnovateOS Init startet...")
        
        # Systeminitialisierung
        self.mount_filesystems()
        self.setup_devices()
        self.start_core_services()
        
        # Überwache Dienste
        try:
            self.monitor_services()
        except Exception as e:
            self.logger.error(f"Kritischer Fehler: {e}")
            self.shutdown()
            sys.exit(1)
            
if __name__ == "__main__":
    init = InnovateInit()
    init.run()
