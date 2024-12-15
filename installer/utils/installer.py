import logging
import os
import wmi
import win32api
import win32file
import win32con
from typing import List, Dict, Optional
import yaml
import subprocess
import shutil
import requests
from pathlib import Path
import hashlib
import json
from datetime import datetime

class InstallerManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.wmi = wmi.WMI()
        self.system_files_url = "https://github.com/InnovateOS/releases/latest/download/system.img"
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
    def get_available_drives(self) -> List[Dict]:
        """Get list of available removable drives"""
        try:
            drives = []
            for drive in self.wmi.Win32_LogicalDisk():
                if drive.DriveType == 2:  # Removable drive
                    drives.append({
                        'letter': drive.DeviceID,
                        'label': drive.VolumeName or 'NO NAME',
                        'size': int(drive.Size),
                        'free_space': int(drive.FreeSpace)
                    })
            return drives
        except Exception as e:
            self.logger.error(f"Error getting drives: {e}")
            return []
            
    def download_system_image(self) -> Optional[Path]:
        """Download the system image"""
        try:
            self.logger.info("Downloading system image...")
            response = requests.get(self.system_files_url, stream=True)
            response.raise_for_status()
            
            image_path = self.temp_dir / "system.img"
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return image_path
            
        except Exception as e:
            self.logger.error(f"Error downloading system image: {e}")
            return None
            
    def verify_image_checksum(self, image_path: Path) -> bool:
        """Verify the downloaded image checksum"""
        try:
            # Download checksum file
            checksum_url = f"{self.system_files_url}.sha256"
            response = requests.get(checksum_url)
            response.raise_for_status()
            expected_checksum = response.text.strip()
            
            # Calculate actual checksum
            sha256_hash = hashlib.sha256()
            with open(image_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            actual_checksum = sha256_hash.hexdigest()
            
            return expected_checksum == actual_checksum
            
        except Exception as e:
            self.logger.error(f"Error verifying checksum: {e}")
            return False
            
    def prepare_drive(self, drive_letter: str) -> bool:
        """Prepare the selected drive for InnovateOS installation"""
        try:
            self.logger.info(f"Preparing drive {drive_letter}")
            
            # Format drive
            format_cmd = f"format {drive_letter} /FS:FAT32 /Q /V:InnovateOS"
            result = subprocess.run(format_cmd, shell=True, capture_output=True)
            if result.returncode != 0:
                raise Exception(f"Format failed: {result.stderr.decode()}")
                
            # Create directory structure
            os.makedirs(f"{drive_letter}/innovateos", exist_ok=True)
            os.makedirs(f"{drive_letter}/innovateos/config", exist_ok=True)
            os.makedirs(f"{drive_letter}/innovateos/data", exist_ok=True)
            os.makedirs(f"{drive_letter}/innovateos/system", exist_ok=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error preparing drive: {e}")
            return False
            
    def write_image_to_drive(self, image_path: Path, drive_letter: str) -> bool:
        """Write system image to drive"""
        try:
            self.logger.info(f"Writing system image to {drive_letter}")
            
            # Use dd for Windows to write image
            dd_cmd = f"dd if={image_path} of=\\\\.\\{drive_letter} bs=4M"
            result = subprocess.run(dd_cmd, shell=True, capture_output=True)
            if result.returncode != 0:
                raise Exception(f"DD failed: {result.stderr.decode()}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing image: {e}")
            return False
            
    def configure_system(self, drive_letter: str, config: Dict) -> bool:
        """Configure the installed system"""
        try:
            self.logger.info("Configuring system")
            config_path = f"{drive_letter}/innovateos/config/system.yaml"
            
            # Add system version and installation date
            config['system']['version'] = "1.0.0"
            config['system']['install_date'] = datetime.now().isoformat()
            
            # Write configuration
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
                
            # Create network configuration
            network_config = {
                'wifi': {
                    'ssid': config['network']['ssid'],
                    'password': config['network']['password']
                }
            }
            with open(f"{drive_letter}/innovateos/config/network.yaml", 'w') as f:
                yaml.dump(network_config, f)
                
            # Create printer configuration
            printer_config = {
                'model': config['printer']['model'],
                'connection': config['printer']['connection'],
                'settings': self._get_printer_defaults(config['printer']['model'])
            }
            with open(f"{drive_letter}/innovateos/config/printer.yaml", 'w') as f:
                yaml.dump(printer_config, f)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring system: {e}")
            return False
            
    def _get_printer_defaults(self, model: str) -> Dict:
        """Get default settings for printer model"""
        # This would be expanded with more models and settings
        defaults = {
            "Prusa i3 MK3S+": {
                "bed_size": {"x": 250, "y": 210, "z": 210},
                "nozzle_diameter": 0.4,
                "max_temp": {"bed": 120, "nozzle": 280}
            },
            "Creality Ender 3": {
                "bed_size": {"x": 220, "y": 220, "z": 250},
                "nozzle_diameter": 0.4,
                "max_temp": {"bed": 110, "nozzle": 260}
            }
        }
        return defaults.get(model, {})
            
    def verify_installation(self, drive_letter: str) -> bool:
        """Verify the installation was successful"""
        try:
            required_files = [
                'innovateos/config/system.yaml',
                'innovateos/config/network.yaml',
                'innovateos/config/printer.yaml',
                'innovateos/system/boot.img',
                'innovateos/system/rootfs.img'
            ]
            
            for file in required_files:
                full_path = f"{drive_letter}/{file}"
                if not os.path.exists(full_path):
                    self.logger.error(f"Missing required file: {file}")
                    return False
                    
            # Verify system.yaml can be loaded
            try:
                with open(f"{drive_letter}/innovateos/config/system.yaml", 'r') as f:
                    yaml.safe_load(f)
            except Exception as e:
                self.logger.error(f"Invalid system configuration: {e}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying installation: {e}")
            return False
            
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.error(f"Error cleaning up: {e}")

    def install_system(self, drive_letter: str, config: Dict) -> bool:
        """Install InnovateOS on the selected drive"""
        try:
            # Download system image
            image_path = self.download_system_image()
            if not image_path:
                return False
            
            # Verify image checksum
            if not self.verify_image_checksum(image_path):
                return False
            
            # Prepare drive
            if not self.prepare_drive(drive_letter):
                return False
            
            # Write image to drive
            if not self.write_image_to_drive(image_path, drive_letter):
                return False
            
            # Configure system
            if not self.configure_system(drive_letter, config):
                return False
            
            # Verify installation
            if not self.verify_installation(drive_letter):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing system: {e}")
            return False

if __name__ == "__main__":
    # Test installation process
    installer = InstallerManager()
    drives = installer.get_available_drives()
    if drives:
        print(f"Found drives: {drives}")
    else:
        print("No removable drives found")
