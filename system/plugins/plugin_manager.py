#!/usr/bin/env python3
import os
import json
import importlib.util
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PluginInfo:
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str]
    enabled: bool
    last_updated: datetime
    config: dict

class PluginManager:
    def __init__(self, plugin_dir: str, config_dir: str):
        self.plugin_dir = plugin_dir
        self.config_dir = config_dir
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_modules = {}
        self.logger = logging.getLogger("PluginManager")
        
        # Ensure directories exist
        os.makedirs(plugin_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize plugin configuration
        self.config_file = os.path.join(config_dir, "plugins.json")
        self.load_plugin_config()

    def load_plugin_config(self):
        """Load plugin configuration from JSON file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                for name, info in config.items():
                    info['last_updated'] = datetime.fromisoformat(info['last_updated'])
                    self.plugins[name] = PluginInfo(**info)

    def save_plugin_config(self):
        """Save plugin configuration to JSON file"""
        config = {name: {
            'name': info.name,
            'version': info.version,
            'author': info.author,
            'description': info.description,
            'dependencies': info.dependencies,
            'enabled': info.enabled,
            'last_updated': info.last_updated.isoformat(),
            'config': info.config
        } for name, info in self.plugins.items()}
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugin directory"""
        discovered = []
        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "plugin.json")):
                discovered.append(item)
        return discovered

    def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin"""
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        manifest_path = os.path.join(plugin_path, "plugin.json")
        
        try:
            # Load plugin manifest
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Check dependencies
            for dep in manifest.get('dependencies', []):
                if dep not in self.plugins or not self.plugins[dep].enabled:
                    self.logger.error(f"Plugin {plugin_name} requires {dep} which is not available")
                    return False
            
            # Load plugin module
            module_path = os.path.join(plugin_path, "main.py")
            spec = importlib.util.spec_from_file_location(plugin_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create plugin info
            plugin_info = PluginInfo(
                name=manifest['name'],
                version=manifest['version'],
                author=manifest['author'],
                description=manifest['description'],
                dependencies=manifest.get('dependencies', []),
                enabled=True,
                last_updated=datetime.now(),
                config=manifest.get('config', {})
            )
            
            self.plugins[plugin_name] = plugin_info
            self.loaded_modules[plugin_name] = module
            self.save_plugin_config()
            
            # Initialize plugin
            if hasattr(module, 'initialize'):
                module.initialize()
            
            self.logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        try:
            if plugin_name in self.loaded_modules:
                module = self.loaded_modules[plugin_name]
                if hasattr(module, 'cleanup'):
                    module.cleanup()
                
                del self.loaded_modules[plugin_name]
                if plugin_name in self.plugins:
                    self.plugins[plugin_name].enabled = False
                    self.save_plugin_config()
                
                self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {str(e)}")
            return False

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin"""
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, PluginInfo]:
        """Get information about all plugins"""
        return self.plugins

    def update_plugin_config(self, plugin_name: str, config: dict) -> bool:
        """Update configuration for a specific plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].config.update(config)
            self.save_plugin_config()
            
            # Notify plugin of config change if supported
            if plugin_name in self.loaded_modules:
                module = self.loaded_modules[plugin_name]
                if hasattr(module, 'config_updated'):
                    module.config_updated(config)
            
            return True
        return False

    def check_updates(self) -> Dict[str, str]:
        """Check for available updates for all plugins"""
        # TODO: Implement update checking logic
        # This would typically involve checking a remote repository
        return {}

    @classmethod
    def refresh_plugins(cls):
        """Aktualisiere die Plugin-Liste"""
        manager = cls("/usr/lib/innovate/plugins", "/etc/innovate/plugins")
        manager.discover_plugins()

    @classmethod
    def get_plugin_list(cls) -> List[Dict]:
        """Hole eine Liste aller Plugins für die Web-Oberfläche"""
        manager = cls("/usr/lib/innovate/plugins", "/etc/innovate/plugins")
        plugins = []
        for name, info in manager.get_all_plugins().items():
            plugins.append({
                'name': info.name,
                'version': info.version,
                'author': info.author,
                'description': info.description,
                'enabled': info.enabled,
                'update_available': False,  # TODO: Implement update check
                'latest_version': None
            })
        return plugins

    @classmethod
    def enable_plugin(cls, plugin_name: str) -> bool:
        """Aktiviere ein Plugin"""
        manager = cls("/usr/lib/innovate/plugins", "/etc/innovate/plugins")
        return manager.load_plugin(plugin_name)

    @classmethod
    def disable_plugin(cls, plugin_name: str) -> bool:
        """Deaktiviere ein Plugin"""
        manager = cls("/usr/lib/innovate/plugins", "/etc/innovate/plugins")
        return manager.unload_plugin(plugin_name)

    @classmethod
    def update_plugin(cls, plugin_name: str, progress_callback=None) -> bool:
        """Aktualisiere ein Plugin"""
        try:
            manager = cls("/usr/lib/innovate/plugins", "/etc/innovate/plugins")
            if progress_callback:
                progress_callback(0, "Prüfe auf Updates...")

            # TODO: Implement actual update logic
            if progress_callback:
                progress_callback(100, "Plugin ist bereits auf dem neuesten Stand")
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(100, f"Fehler beim Update: {str(e)}")
            return False

if __name__ == "__main__":
    manager = PluginManager("/usr/lib/innovate/plugins", "/etc/innovate/plugins")
    manager.discover_plugins()
    print("Verfügbare Plugins:", manager.get_all_plugins())
