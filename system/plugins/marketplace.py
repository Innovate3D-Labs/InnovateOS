import requests
import json
from pathlib import Path
import logging
from typing import Dict, List, Optional
from datetime import datetime

class PluginMarketplace:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_url = "https://marketplace.innovateos.org/api/v1"
        self.cache_dir = Path("cache/marketplace")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_available_plugins(self, category: Optional[str] = None) -> List[Dict]:
        """Get list of available plugins from marketplace"""
        try:
            params = {"category": category} if category else {}
            response = requests.get(f"{self.api_url}/plugins", params=params)
            response.raise_for_status()
            plugins = response.json()
            
            # Cache the results
            self._cache_results("available_plugins", plugins)
            return plugins
        except Exception as e:
            self.logger.error(f"Error fetching plugins: {e}")
            # Return cached results if available
            return self._get_cached_results("available_plugins", [])

    def get_plugin_details(self, plugin_id: str) -> Optional[Dict]:
        """Get detailed information about a specific plugin"""
        try:
            response = requests.get(f"{self.api_url}/plugins/{plugin_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching plugin details: {e}")
            return None

    def download_plugin(self, plugin_id: str, version: str) -> Optional[Path]:
        """Download a specific plugin version"""
        try:
            response = requests.get(
                f"{self.api_url}/plugins/{plugin_id}/download",
                params={"version": version},
                stream=True
            )
            response.raise_for_status()
            
            download_path = Path(f"downloads/plugins/{plugin_id}-{version}.zip")
            download_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return download_path
        except Exception as e:
            self.logger.error(f"Error downloading plugin: {e}")
            return None

    def check_updates(self, installed_plugins: Dict[str, str]) -> Dict[str, str]:
        """Check for available updates for installed plugins"""
        try:
            response = requests.post(
                f"{self.api_url}/plugins/check-updates",
                json=installed_plugins
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
            return {}

    def submit_plugin(self, plugin_data: Dict) -> bool:
        """Submit a new plugin to the marketplace"""
        try:
            response = requests.post(
                f"{self.api_url}/plugins/submit",
                json=plugin_data
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error submitting plugin: {e}")
            return False

    def _cache_results(self, cache_key: str, data: Any) -> None:
        """Cache API results"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            self.logger.error(f"Error caching results: {e}")

    def _get_cached_results(self, cache_key: str, default: Any) -> Any:
        """Get cached results if available"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                # Check if cache is less than 1 hour old
                cache_time = datetime.fromisoformat(cache_data["timestamp"])
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    return cache_data["data"]
            return default
        except Exception as e:
            self.logger.error(f"Error reading cache: {e}")
            return default
