#!/usr/bin/env python3
import os
import sys
import json
import shutil
import tarfile
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class BackupManager:
    def __init__(self):
        self.backup_dir = Path("/var/lib/innovate/backups")
        self.config_dir = Path("/etc/innovate")
        self.data_dir = Path("/var/lib/innovate")
        self.logger = self._setup_logging()
        
        # Erstelle Backup-Verzeichnis falls nicht vorhanden
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logging(self):
        logger = logging.getLogger('BackupManager')
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler('/var/log/innovate_backup.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger
        
    def _create_manifest(self, backup_path: Path) -> Dict:
        """Erstellt ein Manifest für das Backup"""
        return {
            'timestamp': datetime.now().isoformat(),
            'version': self._get_system_version(),
            'files': self._get_backup_files(),
            'checksum': self._calculate_checksum(backup_path)
        }
        
    def _get_system_version(self) -> str:
        """Liest die aktuelle Systemversion"""
        try:
            with open("/etc/innovate/version", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "unknown"
            
    def _get_backup_files(self) -> List[str]:
        """Sammelt alle zu sichernden Dateien"""
        files = []
        # Konfigurationsdateien
        files.extend(str(p) for p in self.config_dir.rglob('*') if p.is_file())
        # Benutzerdaten
        files.extend(str(p) for p in self.data_dir.rglob('*') if p.is_file())
        # Drucker-Konfigurationen
        if Path("/etc/printer").exists():
            files.extend(str(p) for p in Path("/etc/printer").rglob('*') if p.is_file())
        return files
        
    def _calculate_checksum(self, path: Path) -> str:
        """Berechnet SHA256 Checksum einer Datei"""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def create_backup(self, name: str = None) -> bool:
        """Erstellt ein neues Backup"""
        try:
            if name is None:
                name = datetime.now().strftime("%Y%m%d_%H%M%S")
                
            backup_path = self.backup_dir / f"{name}.tar.gz"
            manifest_path = self.backup_dir / f"{name}_manifest.json"
            
            # Erstelle Backup-Archiv
            with tarfile.open(backup_path, "w:gz") as tar:
                for file_path in self._get_backup_files():
                    tar.add(file_path)
                    
            # Erstelle und speichere Manifest
            manifest = self._create_manifest(backup_path)
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
                
            self.logger.info(f"Backup erstellt: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des Backups: {e}")
            return False
            
    def restore_backup(self, name: str) -> bool:
        """Stellt ein Backup wieder her"""
        try:
            backup_path = self.backup_dir / f"{name}.tar.gz"
            manifest_path = self.backup_dir / f"{name}_manifest.json"
            
            if not backup_path.exists() or not manifest_path.exists():
                raise FileNotFoundError(f"Backup {name} nicht gefunden")
                
            # Prüfe Manifest
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                
            # Verifiziere Checksum
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != manifest['checksum']:
                raise ValueError("Backup-Integrität verletzt")
                
            # Erstelle Sicherung des aktuellen Zustands
            temp_backup = self.create_backup("pre_restore")
            if not temp_backup:
                raise Exception("Konnte keine temporäre Sicherung erstellen")
                
            # Stelle Backup wieder her
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall("/")
                
            self.logger.info(f"Backup wiederhergestellt: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Wiederherstellung: {e}")
            return False
            
    def list_backups(self) -> List[Dict]:
        """Listet alle verfügbaren Backups"""
        backups = []
        for manifest_file in self.backup_dir.glob("*_manifest.json"):
            try:
                with open(manifest_file, "r") as f:
                    manifest = json.load(f)
                    name = manifest_file.stem.replace("_manifest", "")
                    backups.append({
                        'name': name,
                        'timestamp': manifest['timestamp'],
                        'version': manifest['version'],
                        'size': os.path.getsize(self.backup_dir / f"{name}.tar.gz")
                    })
            except Exception as e:
                self.logger.error(f"Fehler beim Lesen von {manifest_file}: {e}")
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        
    def cleanup_old_backups(self, keep_count: int = 5):
        """Entfernt alte Backups"""
        backups = self.list_backups()
        if len(backups) > keep_count:
            for backup in backups[keep_count:]:
                try:
                    name = backup['name']
                    os.remove(self.backup_dir / f"{name}.tar.gz")
                    os.remove(self.backup_dir / f"{name}_manifest.json")
                    self.logger.info(f"Altes Backup entfernt: {name}")
                except Exception as e:
                    self.logger.error(f"Fehler beim Entfernen von {name}: {e}")
                    
    @classmethod
    def get_auto_backup_enabled(cls) -> bool:
        """Prüft ob automatische Backups aktiviert sind"""
        try:
            with open("/etc/innovate/backup_config.json", "r") as f:
                config = json.load(f)
                return config.get('auto_backup', False)
        except FileNotFoundError:
            return False

    @classmethod
    def set_auto_backup(cls, enabled: bool, interval: str):
        """Aktiviert oder deaktiviert automatische Backups"""
        config = {
            'auto_backup': enabled,
            'interval': interval
        }
        os.makedirs("/etc/innovate", exist_ok=True)
        with open("/etc/innovate/backup_config.json", "w") as f:
            json.dump(config, f, indent=2)

    @classmethod
    def get_last_backup_time(cls) -> str:
        """Gibt den Zeitpunkt des letzten Backups zurück"""
        try:
            backups = cls().list_backups()
            if backups:
                return backups[0]['timestamp']
            return None
        except Exception:
            return None

    @classmethod
    def get_available_backups(cls) -> List[Dict]:
        """Gibt eine Liste aller verfügbaren Backups zurück"""
        try:
            backups = cls().list_backups()
            return [{
                'id': backup['name'],
                'name': backup['name'],
                'date': backup['timestamp'],
                'size': cls._format_size(backup['size'])
            } for backup in backups]
        except Exception:
            return []

    @staticmethod
    def _format_size(size_in_bytes: int) -> str:
        """Formatiert eine Dateigröße in eine lesbare Form"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.1f} TB"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: backup_manager.py [create|restore|list|cleanup]")
        sys.exit(1)
        
    manager = BackupManager()
    command = sys.argv[1]
    
    if command == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        success = manager.create_backup(name)
        sys.exit(0 if success else 1)
        
    elif command == "restore":
        if len(sys.argv) != 3:
            print("Backup-Namen angeben")
            sys.exit(1)
        success = manager.restore_backup(sys.argv[2])
        sys.exit(0 if success else 1)
        
    elif command == "list":
        backups = manager.list_backups()
        for backup in backups:
            print(f"{backup['name']}: {backup['timestamp']} ({backup['version']})")
        
    elif command == "cleanup":
        keep = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        manager.cleanup_old_backups(keep)
