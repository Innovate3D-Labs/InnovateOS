#!/usr/bin/env python3
import socket
import json
import logging
import threading
import time
from typing import Dict, List, Optional
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf
import netifaces
import requests

class DeviceDiscovery:
    def __init__(self):
        self.logger = self._setup_logging()
        self.discovered_devices = {}
        self.zeroconf = Zeroconf()
        self.browser = None
        self.running = False
        
    def _setup_logging(self):
        logger = logging.getLogger('DeviceDiscovery')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('/var/log/innovate_discovery.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger
        
    def _get_local_ip(self) -> str:
        """Ermittelt die lokale IP-Adresse"""
        try:
            # Versuche Standard-Gateway-Interface zu finden
            gws = netifaces.gateways()
            if 'default' in gws and netifaces.AF_INET in gws['default']:
                interface = gws['default'][netifaces.AF_INET][1]
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    return addrs[netifaces.AF_INET][0]['addr']
        except Exception:
            pass
            
        # Fallback: Verbinde mit externer Adresse
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
            
    def _scan_network_range(self, base_ip: str) -> List[str]:
        """Scannt einen IP-Bereich"""
        network = base_ip.rsplit('.', 1)[0]
        active_ips = []
        
        def check_ip(ip):
            try:
                socket.create_connection((ip, 80), timeout=1)
                active_ips.append(ip)
            except (socket.timeout, socket.error):
                pass
                
        threads = []
        for i in range(1, 255):
            ip = f"{network}.{i}"
            thread = threading.Thread(target=check_ip, args=(ip,))
            thread.start()
            threads.append(thread)
            
        for thread in threads:
            thread.join()
            
        return active_ips
        
    def _check_device_type(self, ip: str) -> Optional[Dict]:
        """Prüft den Gerätetyp über HTTP"""
        try:
            # Versuche API-Endpunkt
            response = requests.get(f"http://{ip}/api/info", timeout=2)
            if response.status_code == 200:
                return response.json()
                
            # Prüfe auf bekannte Drucker-Webinterfaces
            for port in [80, 8080]:
                try:
                    response = requests.get(f"http://{ip}:{port}", timeout=1)
                    content = response.text.lower()
                    
                    # Prüfe auf bekannte Merkmale
                    if any(x in content for x in ['octoprint', 'marlin', 'repetier']):
                        return {
                            'type': '3d_printer',
                            'interface': 'web',
                            'name': 'Unknown Printer'
                        }
                except requests.exceptions.RequestException:
                    continue
                    
        except requests.exceptions.RequestException:
            pass
            
        # Prüfe auf serielle Verbindung
        try:
            import serial
            ser = serial.Serial(ip, 115200, timeout=1)
            ser.write(b"M115\n")  # Marlin-Identifikation
            response = ser.readline().decode()
            ser.close()
            
            if "FIRMWARE_NAME:" in response:
                return {
                    'type': '3d_printer',
                    'interface': 'serial',
                    'name': response.split(':')[1].strip()
                }
        except Exception:
            pass
            
        return None
        
    def register_service(self):
        """Registriert den eigenen Service"""
        info = ServiceInfo(
            "_innovate._tcp.local.",
            f"InnovateOS._innovate._tcp.local.",
            addresses=[socket.inet_aton(self._get_local_ip())],
            port=80,
            properties={
                'version': '1.0.0',
                'type': 'controller'
            }
        )
        self.zeroconf.register_service(info)
        
    def start_discovery(self):
        """Startet die Geräte-Erkennung"""
        self.running = True
        
        # Starte mDNS-Browser
        self.browser = ServiceBrowser(
            self.zeroconf,
            "_innovate._tcp.local.",
            self
        )
        
        # Starte Netzwerk-Scan
        threading.Thread(target=self._continuous_scan).start()
        
    def stop_discovery(self):
        """Stoppt die Geräte-Erkennung"""
        self.running = False
        if self.browser:
            self.browser.cancel()
        self.zeroconf.close()
        
    def _continuous_scan(self):
        """Kontinuierlicher Netzwerk-Scan"""
        while self.running:
            local_ip = self._get_local_ip()
            active_ips = self._scan_network_range(local_ip)
            
            for ip in active_ips:
                if ip not in self.discovered_devices:
                    device_info = self._check_device_type(ip)
                    if device_info:
                        self.discovered_devices[ip] = {
                            **device_info,
                            'ip': ip,
                            'last_seen': time.time(),
                            'available': True
                        }
                        self.logger.info(f"Neues Gerät gefunden: {ip}")
                        
            # Aktualisiere Status
            current_time = time.time()
            for ip, device in list(self.discovered_devices.items()):
                if current_time - device['last_seen'] > 300:  # 5 Minuten
                    device['available'] = False
                    
            time.sleep(60)  # Scan alle 60 Sekunden
            
    def scan_network(self) -> List[Dict]:
        """Einmaliger Netzwerk-Scan"""
        local_ip = self._get_local_ip()
        active_ips = self._scan_network_range(local_ip)
        
        devices = []
        for ip in active_ips:
            device_info = self._check_device_type(ip)
            if device_info:
                devices.append({
                    **device_info,
                    'ip': ip,
                    'available': True
                })
                
        return devices
        
    def get_device_info(self, ip: str) -> Optional[Dict]:
        """Holt Geräteinformationen"""
        return self.discovered_devices.get(ip)
        
    def connect_device(self, ip: str) -> bool:
        """Verbindet mit einem Gerät"""
        device = self.discovered_devices.get(ip)
        if not device or not device['available']:
            return False
            
        try:
            if device['interface'] == 'web':
                # Verbinde über Web-API
                response = requests.post(
                    f"http://{ip}/api/connect",
                    json={'client': 'InnovateOS'},
                    timeout=5
                )
                return response.status_code == 200
                
            elif device['interface'] == 'serial':
                # Verbinde über serielle Schnittstelle
                import serial
                ser = serial.Serial(ip, 115200)
                ser.close()
                return True
                
        except Exception as e:
            self.logger.error(f"Verbindungsfehler zu {ip}: {e}")
            return False
            
    def remove_device(self, ip: str):
        """Entfernt ein Gerät aus der Liste"""
        if ip in self.discovered_devices:
            del self.discovered_devices[ip]
            
if __name__ == "__main__":
    discovery = DeviceDiscovery()
    discovery.start_discovery()
    try:
        while True:
            print("\nGefundene Geräte:")
            for ip, device in discovery.discovered_devices.items():
                print(f"{ip}: {device['type']} ({device['name']})")
            time.sleep(10)
    except KeyboardInterrupt:
        discovery.stop_discovery()
