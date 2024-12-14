#!/usr/bin/env python3
import os
import json
import time
import logging
import subprocess
from typing import Dict, List, Optional
import netifaces
import wifi
from pathlib import Path

class NetworkManager:
    def __init__(self):
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.interfaces = {}
        self.wifi_manager = wifi.Cell()
        
    def _setup_logging(self):
        logger = logging.getLogger('NetworkManager')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('/var/log/innovate_network.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger
        
    def _load_config(self) -> Dict:
        """Lädt die Netzwerkkonfiguration"""
        try:
            with open("/etc/innovate/system.conf", "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            return {}
            
    def discover_interfaces(self):
        """Erkennt verfügbare Netzwerkschnittstellen"""
        self.interfaces = {}
        for iface in netifaces.interfaces():
            if iface != 'lo':  # Ignoriere Loopback
                info = netifaces.ifaddresses(iface)
                self.interfaces[iface] = {
                    'type': 'wireless' if os.path.exists(f"/sys/class/net/{iface}/wireless")
                           else 'ethernet',
                    'addresses': info.get(netifaces.AF_INET, []),
                    'mac': info.get(netifaces.AF_LINK, [{}])[0].get('addr')
                }
                
    def setup_ethernet(self, interface: str):
        """Konfiguriert eine Ethernet-Schnittstelle"""
        try:
            if self.config.get('network', {}).get('dhcp', True):
                subprocess.run(['dhclient', interface], check=True)
            else:
                # Statische IP-Konfiguration
                static_config = self.config.get('network', {})
                subprocess.run([
                    'ip', 'addr', 'add',
                    f"{static_config['ip']}/{static_config['netmask']}",
                    'dev', interface
                ], check=True)
                subprocess.run([
                    'ip', 'route', 'add', 'default',
                    'via', static_config['gateway']
                ], check=True)
                
            self.logger.info(f"Ethernet-Interface {interface} konfiguriert")
            return True
        except Exception as e:
            self.logger.error(f"Fehler bei Ethernet-Konfiguration: {e}")
            return False
            
    def scan_wifi_networks(self, interface: str) -> List[Dict]:
        """Scannt nach verfügbaren WLAN-Netzwerken"""
        try:
            networks = self.wifi_manager.all(interface)
            return [{
                'ssid': network.ssid,
                'signal': network.signal,
                'encryption': network.encryption_type,
                'channel': network.channel
            } for network in networks]
        except Exception as e:
            self.logger.error(f"Fehler beim WLAN-Scan: {e}")
            return []
            
    def connect_wifi(self, interface: str, ssid: str, password: str) -> bool:
        """Verbindet mit einem WLAN-Netzwerk"""
        try:
            # WPA Supplicant Konfiguration
            config = f'''
            network={{
                ssid="{ssid}"
                psk="{password}"
                key_mgmt=WPA-PSK
            }}
            '''
            config_file = f"/etc/wpa_supplicant/wpa_supplicant-{interface}.conf"
            
            with open(config_file, "w") as f:
                f.write(config)
                
            # Starte WPA Supplicant
            subprocess.run([
                'wpa_supplicant',
                '-B',  # Hintergrund
                '-i', interface,
                '-c', config_file
            ], check=True)
            
            # Warte auf Verbindung
            time.sleep(5)
            
            # DHCP
            subprocess.run(['dhclient', interface], check=True)
            
            self.logger.info(f"WLAN-Verbindung hergestellt: {ssid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei WLAN-Verbindung: {e}")
            return False
            
    def setup_firewall(self):
        """Konfiguriert die Firewall"""
        try:
            # Grundlegende Firewall-Regeln
            subprocess.run(['iptables', '-F'])  # Lösche bestehende Regeln
            
            # Standard-Policies
            subprocess.run(['iptables', '-P', 'INPUT', 'DROP'])
            subprocess.run(['iptables', '-P', 'FORWARD', 'DROP'])
            subprocess.run(['iptables', '-P', 'OUTPUT', 'ACCEPT'])
            
            # Erlaube etablierte Verbindungen
            subprocess.run([
                'iptables', '-A', 'INPUT',
                '-m', 'state',
                '--state', 'ESTABLISHED,RELATED',
                '-j', 'ACCEPT'
            ])
            
            # Erlaube Loopback
            subprocess.run(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'])
            
            # Erlaube konfigurierte Ports
            allowed_ports = self.config.get('security', {}).get('allowed_ports', [80, 443])
            for port in allowed_ports:
                subprocess.run([
                    'iptables', '-A', 'INPUT',
                    '-p', 'tcp',
                    '--dport', str(port),
                    '-j', 'ACCEPT'
                ])
                
            self.logger.info("Firewall konfiguriert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Firewall-Konfiguration: {e}")
            return False
            
    def monitor_connections(self):
        """Überwacht Netzwerkverbindungen"""
        while True:
            self.discover_interfaces()
            for iface, info in self.interfaces.items():
                if not info['addresses']:
                    self.logger.warning(f"Interface {iface} hat keine IP-Adresse")
                    if info['type'] == 'ethernet':
                        self.setup_ethernet(iface)
                    # Bei WLAN: Versuche gespeicherte Verbindung
                    
            time.sleep(30)  # Prüfe alle 30 Sekunden
            
    def run(self):
        """Hauptmethode"""
        self.logger.info("Netzwerk-Manager wird gestartet...")
        
        # Initialisierung
        self.discover_interfaces()
        
        # Konfiguriere Ethernet-Interfaces
        for iface, info in self.interfaces.items():
            if info['type'] == 'ethernet':
                self.setup_ethernet(iface)
                
        # Firewall einrichten
        if self.config.get('security', {}).get('enable_firewall', True):
            self.setup_firewall()
            
        # Starte Überwachung
        self.monitor_connections()
        
if __name__ == "__main__":
    manager = NetworkManager()
    manager.run()
