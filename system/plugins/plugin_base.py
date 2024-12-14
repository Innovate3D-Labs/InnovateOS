from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

class PluginBase(ABC):
    """Base class for all InnovateOS plugins"""
    
    def __init__(self, plugin_id: str, version: str):
        self.plugin_id = plugin_id
        self.version = version
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"plugin.{plugin_id}")
        self.enabled = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin"""
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up resources when plugin is disabled"""
        pass

    def load_config(self, config_path: Optional[Path] = None) -> bool:
        """Load plugin configuration"""
        try:
            if config_path is None:
                config_path = Path(f"config/plugins/{self.plugin_id}.json")
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return False

    def save_config(self, config_path: Optional[Path] = None) -> bool:
        """Save plugin configuration"""
        try:
            if config_path is None:
                config_path = Path(f"config/plugins/{self.plugin_id}.json")
            
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            return False

    @abstractmethod
    def get_settings_schema(self) -> Dict[str, Any]:
        """Return JSON schema for plugin settings"""
        pass

    @abstractmethod
    def validate_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate plugin settings"""
        pass

    def get_api_endpoints(self) -> Dict[str, Any]:
        """Return API endpoints provided by this plugin"""
        return {}

    def get_web_routes(self) -> Dict[str, Any]:
        """Return web routes provided by this plugin"""
        return {}

    def get_dependencies(self) -> Dict[str, str]:
        """Return plugin dependencies"""
        return {}
