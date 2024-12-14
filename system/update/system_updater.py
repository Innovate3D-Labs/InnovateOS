import os
import json
import logging
import requests
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class UpdateInfo:
    version: str
    release_date: datetime
    description: str
    changes: List[str]
    size_bytes: int
    checksum: str
    download_url: str
    requires_restart: bool

class SystemUpdater:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "update.json")
        self.logger = logging.getLogger("SystemUpdater")
        self.update_lock = threading.Lock()
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize update status
        self.current_update = None
        self.update_progress = 0
        self.update_status = "idle"
        self.last_check = None
        self.available_update = None

    def load_config(self) -> dict:
        """Load update configuration"""
        default_config = {
            'update_channel': 'stable',
            'auto_check': True,
            'auto_download': False,
            'auto_install': False,
            'check_interval_hours': 24,
            'update_server': 'https://updates.innovateos.org',
            'current_version': '1.0.0'
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        return default_config

    def save_config(self):
        """Save update configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def check_for_updates(self) -> Optional[UpdateInfo]:
        """Check for available system updates"""
        try:
            self.last_check = datetime.now()
            
            # Make request to update server
            response = requests.get(
                f"{self.config['update_server']}/api/v1/updates/check",
                params={
                    'channel': self.config['update_channel'],
                    'current_version': self.config['current_version'],
                    'system_info': self._get_system_info()
                }
            )
            response.raise_for_status()
            
            update_data = response.json()
            if update_data['update_available']:
                self.available_update = UpdateInfo(
                    version=update_data['version'],
                    release_date=datetime.fromisoformat(update_data['release_date']),
                    description=update_data['description'],
                    changes=update_data['changes'],
                    size_bytes=update_data['size_bytes'],
                    checksum=update_data['checksum'],
                    download_url=update_data['download_url'],
                    requires_restart=update_data['requires_restart']
                )
                return self.available_update
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to check for updates: {str(e)}")
            return None

    def download_update(self, update_info: UpdateInfo) -> bool:
        """Download system update"""
        if self.update_status != "idle":
            return False
        
        try:
            self.update_status = "downloading"
            self.update_progress = 0
            self.current_update = update_info
            
            # Create temporary directory for download
            temp_dir = os.path.join(self.config_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Download update file
            response = requests.get(update_info.download_url, stream=True)
            response.raise_for_status()
            
            file_path = os.path.join(temp_dir, f"update_{update_info.version}.zip")
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.update_progress = int((downloaded / total_size) * 100)
            
            # Verify checksum
            if not self._verify_checksum(file_path, update_info.checksum):
                raise ValueError("Update file checksum verification failed")
            
            self.update_status = "ready"
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download update: {str(e)}")
            self.update_status = "error"
            return False

    def install_update(self, update_info: UpdateInfo) -> bool:
        """Install downloaded system update"""
        if self.update_status != "ready":
            return False
        
        try:
            with self.update_lock:
                self.update_status = "installing"
                self.update_progress = 0
                
                # Create backup before update
                if not self._create_backup():
                    raise ValueError("Failed to create backup before update")
                
                # Extract and install update
                temp_dir = os.path.join(self.config_dir, "temp")
                update_file = os.path.join(temp_dir, f"update_{update_info.version}.zip")
                
                # Run update script
                result = subprocess.run(
                    ["sudo", "innovate-update", "install", update_file],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise ValueError(f"Update installation failed: {result.stderr}")
                
                # Update configuration
                self.config['current_version'] = update_info.version
                self.save_config()
                
                self.update_status = "completed"
                self.update_progress = 100
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to install update: {str(e)}")
            self.update_status = "error"
            return False

    def rollback_update(self) -> bool:
        """Rollback the last installed update"""
        try:
            with self.update_lock:
                # Find latest backup
                backup_dir = os.path.join(self.config_dir, "backups")
                backups = sorted(os.listdir(backup_dir), reverse=True)
                
                if not backups:
                    raise ValueError("No backup found for rollback")
                
                latest_backup = os.path.join(backup_dir, backups[0])
                
                # Run rollback script
                result = subprocess.run(
                    ["sudo", "innovate-update", "rollback", latest_backup],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise ValueError(f"Update rollback failed: {result.stderr}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to rollback update: {str(e)}")
            return False

    def get_update_status(self) -> Dict:
        """Get current update status"""
        return {
            'status': self.update_status,
            'progress': self.update_progress,
            'current_version': self.config['current_version'],
            'update_channel': self.config['update_channel'],
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'available_update': {
                'version': self.available_update.version,
                'release_date': self.available_update.release_date.isoformat(),
                'description': self.available_update.description,
                'changes': self.available_update.changes,
                'size_bytes': self.available_update.size_bytes,
                'requires_restart': self.available_update.requires_restart
            } if self.available_update else None
        }

    def _get_system_info(self) -> Dict:
        """Get system information for update check"""
        try:
            import psutil
            return {
                'os_version': os.uname().version,
                'architecture': os.uname().machine,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'disk_space': psutil.disk_usage('/').total
            }
        except Exception:
            return {}

    def _verify_checksum(self, file_path: str, expected_checksum: str) -> bool:
        """Verify file checksum"""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest() == expected_checksum

    def _create_backup(self) -> bool:
        """Create system backup before update"""
        try:
            backup_dir = os.path.join(self.config_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(backup_dir, backup_name)
            
            result = subprocess.run(
                ["sudo", "innovate-backup", "create", backup_path],
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {str(e)}")
            return False

    def set_update_channel(self, channel: str) -> bool:
        """Change update channel"""
        if channel not in ['stable', 'beta', 'development']:
            return False
        
        self.config['update_channel'] = channel
        self.save_config()
        return True

    def set_auto_update(self, auto_check: bool, auto_download: bool, auto_install: bool) -> bool:
        """Configure automatic update settings"""
        try:
            self.config.update({
                'auto_check': auto_check,
                'auto_download': auto_download,
                'auto_install': auto_install
            })
            self.save_config()
            return True
        except Exception as e:
            self.logger.error(f"Failed to set auto update settings: {str(e)}")
            return False

    @classmethod
    def get_current_version(cls) -> str:
        """Get the current system version"""
        try:
            updater = cls("/etc/innovate/update")
            return updater.config['current_version']
        except Exception:
            return "unknown"

    @classmethod
    def get_update_channel(cls) -> str:
        """Get the current update channel"""
        try:
            updater = cls("/etc/innovate/update")
            return updater.config['update_channel']
        except Exception:
            return "stable"

    @classmethod
    def get_auto_check(cls) -> bool:
        """Get auto check setting"""
        try:
            updater = cls("/etc/innovate/update")
            return updater.config['auto_check']
        except Exception:
            return True

    @classmethod
    def get_auto_download(cls) -> bool:
        """Get auto download setting"""
        try:
            updater = cls("/etc/innovate/update")
            return updater.config['auto_download']
        except Exception:
            return False

    @classmethod
    def get_auto_install(cls) -> bool:
        """Get auto install setting"""
        try:
            updater = cls("/etc/innovate/update")
            return updater.config['auto_install']
        except Exception:
            return False

    @classmethod
    def is_update_available(cls) -> bool:
        """Check if an update is available"""
        try:
            updater = cls("/etc/innovate/update")
            return updater.available_update is not None
        except Exception:
            return False

    @classmethod
    def check_updates(cls, progress_callback=None):
        """Check for updates with progress callback"""
        try:
            updater = cls("/etc/innovate/update")
            if progress_callback:
                progress_callback(0, "Suche nach Updates...")
            update = updater.check_for_updates()
            if update:
                if progress_callback:
                    progress_callback(100, f"Update auf Version {update.version} verfügbar")
            else:
                if progress_callback:
                    progress_callback(100, "System ist auf dem neuesten Stand")
        except Exception as e:
            if progress_callback:
                progress_callback(100, f"Fehler bei der Update-Suche: {str(e)}")

    @classmethod
    def install_update(cls, progress_callback=None):
        """Install available update with progress callback"""
        try:
            updater = cls("/etc/innovate/update")
            if not updater.available_update:
                if progress_callback:
                    progress_callback(100, "Kein Update verfügbar")
                return

            if progress_callback:
                progress_callback(0, "Lade Update herunter...")

            if updater.download_update(updater.available_update):
                if progress_callback:
                    progress_callback(50, "Installiere Update...")

                if updater.install_update(updater.available_update):
                    if progress_callback:
                        progress_callback(100, "Update erfolgreich installiert")
                else:
                    if progress_callback:
                        progress_callback(100, "Fehler bei der Update-Installation")
            else:
                if progress_callback:
                    progress_callback(100, "Fehler beim Download des Updates")
        except Exception as e:
            if progress_callback:
                progress_callback(100, f"Fehler beim Update: {str(e)}")

if __name__ == "__main__":
    updater = SystemUpdater("/etc/innovate/update")
    print(updater.get_update_status())
