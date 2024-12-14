#!/usr/bin/env python3
import click
import json
import sys
import os
from typing import Dict
from tabulate import tabulate
from pathlib import Path

class InnovateCLI:
    def __init__(self):
        self.config_dir = Path("/etc/innovate")
        
    def _load_config(self) -> Dict:
        """Lädt die Systemkonfiguration"""
        try:
            with open(self.config_dir / "system.conf", "r") as f:
                return json.load(f)
        except Exception:
            return {}

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """InnovateOS Kommandozeilen-Interface"""
    pass

# System-Befehle
@cli.group()
def system():
    """System-Verwaltung"""
    pass

@system.command()
def status():
    """Zeigt den Systemstatus"""
    from system.monitoring.system_monitor import SystemMonitor
    monitor = SystemMonitor()
    metrics = monitor.metrics
    
    table = [
        ["CPU-Auslastung", f"{metrics['cpu_percent']}%"],
        ["RAM-Auslastung", f"{metrics['memory_percent']}%"],
        ["Festplatten-Auslastung", f"{metrics['disk_percent']}%"],
        ["Temperatur", f"{metrics.get('temperature', 'N/A')}°C"],
        ["Uptime", f"{metrics['uptime']} Sekunden"]
    ]
    
    click.echo(tabulate(table, headers=["Metrik", "Wert"], tablefmt="grid"))

@system.command()
@click.argument('log_type', type=click.Choice(['system', 'network', 'update']))
@click.option('--lines', '-n', default=10, help='Anzahl der Zeilen')
def logs(log_type, lines):
    """Zeigt Systemlogs an"""
    log_files = {
        'system': '/var/log/innovate_init.log',
        'network': '/var/log/innovate_network.log',
        'update': '/var/log/innovate_update.log'
    }
    
    with open(log_files[log_type], 'r') as f:
        click.echo(f"\nLetzte {lines} Zeilen von {log_type}:")
        for line in f.readlines()[-lines:]:
            click.echo(line.strip())

# Drucker-Befehle
@cli.group()
def printer():
    """Drucker-Verwaltung"""
    pass

@printer.command()
def list():
    """Listet alle Drucker auf"""
    from kernel.core.kernel import InnovateKernel
    kernel = InnovateKernel()
    
    printers = []
    for device in kernel.devices.values():
        printers.append([
            device.id,
            device.name,
            device.status,
            f"{device.temperature.hotend}°C",
            f"{device.progress:.1f}%" if device.status == "printing" else "N/A"
        ])
    
    click.echo(tabulate(printers,
                       headers=["ID", "Name", "Status", "Temperatur", "Fortschritt"],
                       tablefmt="grid"))

@printer.command()
@click.argument('printer_id')
@click.argument('command')
def send(printer_id, command):
    """Sendet einen Befehl an einen Drucker"""
    from kernel.core.kernel import InnovateKernel
    kernel = InnovateKernel()
    
    printer = kernel.get_device(printer_id)
    if not printer:
        click.echo(f"Fehler: Drucker {printer_id} nicht gefunden", err=True)
        sys.exit(1)
        
    try:
        result = printer.send_command(command)
        click.echo(f"Befehl gesendet. Antwort: {result}")
    except Exception as e:
        click.echo(f"Fehler: {e}", err=True)
        sys.exit(1)

# Plugin-Befehle
@cli.group()
def plugin():
    """Plugin-Verwaltung"""
    pass

@plugin.command()
def list():
    """Listet alle Plugins auf"""
    from system.plugins.plugin_manager import PluginManager
    manager = PluginManager()
    
    plugins = []
    for plugin in manager.list_plugins():
        plugins.append([
            plugin['name'],
            plugin['version'],
            "Aktiv" if plugin['enabled'] else "Inaktiv",
            plugin['description']
        ])
    
    click.echo(tabulate(plugins,
                       headers=["Name", "Version", "Status", "Beschreibung"],
                       tablefmt="grid"))

@plugin.command()
@click.argument('plugin_name')
def enable(plugin_name):
    """Aktiviert ein Plugin"""
    from system.plugins.plugin_manager import PluginManager
    manager = PluginManager()
    
    if manager.enable_plugin(plugin_name):
        click.echo(f"Plugin {plugin_name} aktiviert")
    else:
        click.echo(f"Fehler beim Aktivieren von {plugin_name}", err=True)
        sys.exit(1)

@plugin.command()
@click.argument('plugin_name')
def disable(plugin_name):
    """Deaktiviert ein Plugin"""
    from system.plugins.plugin_manager import PluginManager
    manager = PluginManager()
    
    if manager.disable_plugin(plugin_name):
        click.echo(f"Plugin {plugin_name} deaktiviert")
    else:
        click.echo(f"Fehler beim Deaktivieren von {plugin_name}", err=True)
        sys.exit(1)

# Geräte-Discovery
@cli.group()
def discover():
    """Geräte-Erkennung"""
    pass

@discover.command()
def scan():
    """Scannt nach verfügbaren Geräten"""
    from system.discovery.device_discovery import DeviceDiscovery
    discovery = DeviceDiscovery()
    
    click.echo("Scanne nach Geräten...")
    devices = discovery.scan_network()
    
    if not devices:
        click.echo("Keine Geräte gefunden")
        return
        
    table = []
    for device in devices:
        table.append([
            device['ip'],
            device['type'],
            device['name'],
            "Ja" if device['available'] else "Nein"
        ])
    
    click.echo(tabulate(table,
                       headers=["IP", "Typ", "Name", "Verfügbar"],
                       tablefmt="grid"))

@discover.command()
@click.argument('device_ip')
def connect(device_ip):
    """Verbindet mit einem erkannten Gerät"""
    from system.discovery.device_discovery import DeviceDiscovery
    discovery = DeviceDiscovery()
    
    click.echo(f"Verbinde mit {device_ip}...")
    if discovery.connect_device(device_ip):
        click.echo("Verbindung hergestellt")
    else:
        click.echo("Verbindung fehlgeschlagen", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()
