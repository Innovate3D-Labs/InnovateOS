import logging
from pathlib import Path
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class MaterialProfile:
    name: str
    type: str  # PLA, ABS, PETG, etc.
    brand: Optional[str]
    nozzle_temp: int
    bed_temp: int
    fan_speed: int  # 0-100%
    flow_rate: int  # Percentage
    retraction_distance: float
    retraction_speed: int
    notes: Optional[str]

class MaterialProfileManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.profiles_file = config_dir / "material_profiles.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.profiles: Dict[str, MaterialProfile] = {}
        self._load_profiles()

    def _load_profiles(self):
        """Load material profiles from file"""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    self.profiles = {
                        name: MaterialProfile(**profile_data)
                        for name, profile_data in data.items()
                    }
            except Exception as e:
                self.logger.error(f"Error loading profiles: {e}")

    def _save_profiles(self):
        """Save material profiles to file"""
        try:
            data = {
                name: {
                    "name": profile.name,
                    "type": profile.type,
                    "brand": profile.brand,
                    "nozzle_temp": profile.nozzle_temp,
                    "bed_temp": profile.bed_temp,
                    "fan_speed": profile.fan_speed,
                    "flow_rate": profile.flow_rate,
                    "retraction_distance": profile.retraction_distance,
                    "retraction_speed": profile.retraction_speed,
                    "notes": profile.notes
                }
                for name, profile in self.profiles.items()
            }
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving profiles: {e}")

    def add_profile(self, profile: MaterialProfile) -> bool:
        """Add or update a material profile"""
        try:
            self.profiles[profile.name] = profile
            self._save_profiles()
            return True
        except Exception as e:
            self.logger.error(f"Error adding profile: {e}")
            return False

    def get_profile(self, name: str) -> Optional[MaterialProfile]:
        """Get a specific material profile"""
        return self.profiles.get(name)

    def list_profiles(self) -> List[str]:
        """List all available material profiles"""
        return list(self.profiles.keys())

    def delete_profile(self, name: str) -> bool:
        """Delete a material profile"""
        try:
            if name in self.profiles:
                del self.profiles[name]
                self._save_profiles()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting profile: {e}")
            return False

    def get_recommended_settings(self, material_type: str) -> Dict:
        """Get recommended settings for a material type"""
        recommendations = {
            "PLA": {
                "nozzle_temp": 200,
                "bed_temp": 60,
                "fan_speed": 100,
                "flow_rate": 100,
                "retraction_distance": 6.5,
                "retraction_speed": 25
            },
            "ABS": {
                "nozzle_temp": 230,
                "bed_temp": 100,
                "fan_speed": 0,
                "flow_rate": 100,
                "retraction_distance": 5.0,
                "retraction_speed": 30
            },
            "PETG": {
                "nozzle_temp": 240,
                "bed_temp": 80,
                "fan_speed": 50,
                "flow_rate": 95,
                "retraction_distance": 5.5,
                "retraction_speed": 25
            }
        }
        return recommendations.get(material_type.upper(), {})

if __name__ == "__main__":
    # Example usage
    profile_manager = MaterialProfileManager(Path("config/materials"))
    
    # Create a new profile
    pla_profile = MaterialProfile(
        name="Generic PLA",
        type="PLA",
        brand="Generic",
        nozzle_temp=200,
        bed_temp=60,
        fan_speed=100,
        flow_rate=100,
        retraction_distance=6.5,
        retraction_speed=25,
        notes="Standard PLA settings"
    )
    
    profile_manager.add_profile(pla_profile)
    print("Available profiles:", profile_manager.list_profiles())
