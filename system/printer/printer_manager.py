import os
import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TempProfile:
    name: str
    bed_temp: int
    nozzle_temp: int

@dataclass
class SafetySettings:
    thermal_runaway: bool
    endstop_check: bool
    max_temp: int
    max_speed: int

@dataclass
class StepsPerMM:
    x: float
    y: float
    z: float
    e: float

class PrinterManager:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "printer.json")
        self.logger = logging.getLogger("PrinterManager")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize printer status
        self.current_temp = {'bed': 0, 'nozzle': 0}
        self.target_temp = {'bed': 0, 'nozzle': 0}
        self.position = {'x': 0, 'y': 0, 'z': 0, 'e': 0}
        self.is_homed = {'x': False, 'y': False, 'z': False}

    def load_config(self) -> dict:
        """Load printer configuration"""
        default_config = {
            'name': 'My 3D Printer',
            'model': 'Generic Printer',
            'firmware_version': '1.0.0',
            'z_offset': 0.0,
            'steps_per_mm': {
                'x': 80.0,
                'y': 80.0,
                'z': 400.0,
                'e': 93.0
            },
            'temp_profiles': [
                {
                    'name': 'PLA',
                    'bed_temp': 60,
                    'nozzle_temp': 200
                },
                {
                    'name': 'PETG',
                    'bed_temp': 80,
                    'nozzle_temp': 240
                },
                {
                    'name': 'ABS',
                    'bed_temp': 100,
                    'nozzle_temp': 250
                }
            ],
            'safety': {
                'thermal_runaway': True,
                'endstop_check': True,
                'max_temp': 260,
                'max_speed': 300
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        return default_config

    def save_config(self):
        """Save printer configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    @classmethod
    def get_current_printer(cls) -> Dict:
        """Get current printer configuration"""
        manager = cls("/etc/innovate/printer")
        return manager.config

    @classmethod
    def update_printer_config(cls, config: Dict):
        """Update printer configuration"""
        manager = cls("/etc/innovate/printer")
        manager.config.update({
            'name': config['name'],
            'model': config['model']
        })
        manager.save_config()
        manager._send_gcode("M503")  # Request settings from printer

    @classmethod
    def move_to_level_point(cls, point: int):
        """Move to bed leveling point"""
        manager = cls("/etc/innovate/printer")
        if not all(manager.is_homed.values()):
            manager._send_gcode("G28")  # Home all axes
        
        # Calculate leveling points based on bed size
        bed_size = manager._get_bed_size()
        margin = 30  # mm from edge
        points = {
            1: (margin, margin),
            2: (bed_size['x'] - margin, margin),
            3: (bed_size['x'] - margin, bed_size['y'] - margin),
            4: (margin, bed_size['y'] - margin),
            5: (bed_size['x'] / 2, bed_size['y'] / 2)
        }
        
        if point in points:
            x, y = points[point]
            manager._send_gcode(f"G0 Z5")  # Lift nozzle
            manager._send_gcode(f"G0 X{x} Y{y}")  # Move to point
            manager._send_gcode(f"G0 Z0")  # Lower nozzle

    @classmethod
    def start_auto_leveling(cls):
        """Start automatic bed leveling"""
        manager = cls("/etc/innovate/printer")
        manager._send_gcode("G28")  # Home all axes
        manager._send_gcode("G29")  # Start auto bed leveling

    @classmethod
    def update_calibration(cls, calibration: Dict):
        """Update printer calibration"""
        manager = cls("/etc/innovate/printer")
        manager.config['z_offset'] = calibration['z_offset']
        manager.config['steps_per_mm'] = calibration['steps_per_mm']
        manager.save_config()
        
        # Update printer settings
        manager._send_gcode(f"M851 Z{calibration['z_offset']}")  # Set Z offset
        for axis, steps in calibration['steps_per_mm'].items():
            manager._send_gcode(f"M92 {axis.upper()}{steps}")  # Set steps/mm
        manager._send_gcode("M500")  # Save to EEPROM

    @classmethod
    def update_temp_profiles(cls, profiles: List[Dict]):
        """Update temperature profiles"""
        manager = cls("/etc/innovate/printer")
        manager.config['temp_profiles'] = profiles
        manager.save_config()

    @classmethod
    def update_safety_settings(cls, settings: Dict):
        """Update safety settings"""
        manager = cls("/etc/innovate/printer")
        manager.config['safety'] = settings
        manager.save_config()
        
        # Update printer settings
        if settings['thermal_runaway']:
            manager._send_gcode("M911")  # Enable thermal runaway protection
        else:
            manager._send_gcode("M912")  # Disable thermal runaway protection
        manager._send_gcode(f"M143 S{settings['max_temp']}")  # Set max temp
        manager._send_gcode("M500")  # Save to EEPROM

    def _send_gcode(self, command: str):
        """Send G-code command to printer"""
        # TODO: Implement actual printer communication
        self.logger.info(f"Sending G-code: {command}")

    def _get_bed_size(self) -> Dict[str, float]:
        """Get printer bed size"""
        # TODO: Get actual bed size from printer
        return {'x': 200, 'y': 200}  # Default size
