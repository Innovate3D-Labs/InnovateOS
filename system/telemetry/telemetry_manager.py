import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import psutil
import platform
from dataclasses import dataclass, asdict

@dataclass
class TelemetryData:
    system_id: str
    timestamp: str
    os_info: Dict
    cpu_usage: float
    memory_usage: Dict
    print_stats: Dict
    error_counts: Dict
    feature_usage: Dict
    anonymous: bool

class TelemetryManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.telemetry_file = data_dir / "telemetry_data.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.system_id = self._generate_system_id()
        self.opt_in = self._load_opt_in_status()

    def _generate_system_id(self) -> str:
        """Generate a unique system ID"""
        system_info = platform.node() + platform.machine()
        return hashlib.md5(system_info.encode()).hexdigest()

    def _load_opt_in_status(self) -> bool:
        """Load telemetry opt-in status"""
        opt_in_file = self.data_dir / "telemetry_opt_in.json"
        if opt_in_file.exists():
            try:
                with open(opt_in_file, 'r') as f:
                    data = json.load(f)
                return data.get("opt_in", False)
            except Exception as e:
                self.logger.error(f"Error loading opt-in status: {e}")
                return False
        return False

    def set_opt_in_status(self, opt_in: bool) -> bool:
        """Set telemetry opt-in status"""
        try:
            opt_in_file = self.data_dir / "telemetry_opt_in.json"
            with open(opt_in_file, 'w') as f:
                json.dump({"opt_in": opt_in}, f)
            self.opt_in = opt_in
            return True
        except Exception as e:
            self.logger.error(f"Error saving opt-in status: {e}")
            return False

    def collect_system_metrics(self) -> Dict:
        """Collect system metrics"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory": dict(psutil.virtual_memory()._asdict()),
                "disk": dict(psutil.disk_usage('/')._asdict()),
                "network": {
                    k: v for k, v in psutil.net_io_counters()._asdict().items()
                    if k in ['bytes_sent', 'bytes_recv']
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}

    def collect_print_stats(self) -> Dict:
        """Collect 3D printing statistics"""
        try:
            # This would be integrated with your printer management system
            return {
                "total_prints": 0,
                "successful_prints": 0,
                "failed_prints": 0,
                "print_time": 0,
                "material_usage": {}
            }
        except Exception as e:
            self.logger.error(f"Error collecting print stats: {e}")
            return {}

    def collect_error_stats(self) -> Dict:
        """Collect error statistics"""
        try:
            # This would be integrated with your error logging system
            return {
                "connection_errors": 0,
                "print_errors": 0,
                "system_errors": 0
            }
        except Exception as e:
            self.logger.error(f"Error collecting error stats: {e}")
            return {}

    def collect_feature_usage(self) -> Dict:
        """Collect feature usage statistics"""
        try:
            # This would be integrated with your feature tracking system
            return {
                "ai_monitoring": 0,
                "remote_control": 0,
                "plugin_usage": {}
            }
        except Exception as e:
            self.logger.error(f"Error collecting feature usage: {e}")
            return {}

    def collect_telemetry(self, anonymous: bool = True) -> Optional[TelemetryData]:
        """Collect all telemetry data"""
        if not self.opt_in:
            return None

        try:
            telemetry = TelemetryData(
                system_id=self.system_id if not anonymous else "anonymous",
                timestamp=datetime.now().isoformat(),
                os_info={
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version()
                } if not anonymous else {},
                cpu_usage=psutil.cpu_percent(),
                memory_usage=self.collect_system_metrics(),
                print_stats=self.collect_print_stats(),
                error_counts=self.collect_error_stats(),
                feature_usage=self.collect_feature_usage(),
                anonymous=anonymous
            )
            return telemetry
            
        except Exception as e:
            self.logger.error(f"Error collecting telemetry: {e}")
            return None

    def save_telemetry(self, data: TelemetryData) -> bool:
        """Save telemetry data"""
        try:
            if self.telemetry_file.exists():
                with open(self.telemetry_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
                
            existing_data.append(asdict(data))
            
            with open(self.telemetry_file, 'w') as f:
                json.dump(existing_data, f, indent=4)
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving telemetry: {e}")
            return False

    def get_telemetry_summary(self) -> Dict:
        """Get summary of collected telemetry data"""
        try:
            if not self.telemetry_file.exists():
                return {}
                
            with open(self.telemetry_file, 'r') as f:
                data = json.load(f)
                
            if not data:
                return {}
                
            latest = data[-1]
            return {
                "last_collection": latest["timestamp"],
                "system_metrics": {
                    "cpu_usage": latest["cpu_usage"],
                    "memory_usage": latest["memory_usage"].get("percent", 0)
                },
                "print_stats": latest["print_stats"],
                "error_counts": latest["error_counts"]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting telemetry summary: {e}")
            return {}

if __name__ == "__main__":
    # Example usage
    telemetry = TelemetryManager(Path("data/telemetry"))
    
    # Set opt-in status (user must explicitly opt-in)
    telemetry.set_opt_in_status(True)
    
    # Collect and save telemetry
    data = telemetry.collect_telemetry(anonymous=True)
    if data:
        telemetry.save_telemetry(data)
        
    # Get summary
    summary = telemetry.get_telemetry_summary()
    print("Telemetry Summary:", summary)
