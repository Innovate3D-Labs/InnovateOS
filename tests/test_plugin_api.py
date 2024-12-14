import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from system.plugins.plugin_base import PluginBase
from system.plugins.plugin_manager import PluginManager
from system.plugins.marketplace import PluginMarketplace

class TestPlugin(PluginBase):
    """Test plugin implementation"""
    def __init__(self):
        super().__init__("test_plugin", "1.0.0")
        
    def initialize(self):
        return True
        
    def cleanup(self):
        return True
        
    def get_settings_schema(self):
        return {
            "type": "object",
            "properties": {
                "test_setting": {
                    "type": "string"
                }
            }
        }
        
    def validate_settings(self, settings):
        return True

@pytest.fixture
def plugin_manager():
    """Create a plugin manager instance for testing"""
    return PluginManager()

@pytest.fixture
def marketplace():
    """Create a marketplace instance for testing"""
    return PluginMarketplace()

def test_plugin_installation(plugin_manager):
    """Test plugin installation process"""
    test_plugin = TestPlugin()
    
    # Test plugin installation
    assert plugin_manager.install_plugin(test_plugin)
    assert test_plugin.plugin_id in plugin_manager.get_installed_plugins()
    
    # Test plugin initialization
    assert plugin_manager.initialize_plugin(test_plugin.plugin_id)
    assert plugin_manager.is_plugin_enabled(test_plugin.plugin_id)

def test_plugin_configuration(plugin_manager):
    """Test plugin configuration management"""
    test_plugin = TestPlugin()
    plugin_manager.install_plugin(test_plugin)
    
    # Test configuration saving
    test_config = {"test_setting": "test_value"}
    assert plugin_manager.save_plugin_config(test_plugin.plugin_id, test_config)
    
    # Test configuration loading
    loaded_config = plugin_manager.get_plugin_config(test_plugin.plugin_id)
    assert loaded_config == test_config

def test_plugin_dependencies(plugin_manager):
    """Test plugin dependency management"""
    test_plugin = TestPlugin()
    test_plugin.get_dependencies = Mock(return_value={
        "required_plugin": ">=1.0.0"
    })
    
    # Test dependency validation
    with pytest.raises(Exception):
        plugin_manager.validate_dependencies(test_plugin)
    
    # Mock required plugin installation
    required_plugin = TestPlugin()
    required_plugin.plugin_id = "required_plugin"
    required_plugin.version = "1.0.0"
    plugin_manager.install_plugin(required_plugin)
    
    # Now validation should pass
    assert plugin_manager.validate_dependencies(test_plugin)

@pytest.mark.asyncio
async def test_marketplace_api(marketplace):
    """Test marketplace API interactions"""
    # Mock API response
    mock_plugins = [
        {
            "id": "test_plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "Test Author"
        }
    ]
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_plugins
        mock_get.return_value.status_code = 200
        
        # Test plugin listing
        plugins = marketplace.get_available_plugins()
        assert len(plugins) == 1
        assert plugins[0]["id"] == "test_plugin"

def test_plugin_update(plugin_manager, marketplace):
    """Test plugin update process"""
    test_plugin = TestPlugin()
    plugin_manager.install_plugin(test_plugin)
    
    # Mock new version available
    with patch.object(marketplace, 'check_updates') as mock_check:
        mock_check.return_value = {
            test_plugin.plugin_id: "2.0.0"
        }
        
        # Test update check
        updates = plugin_manager.check_updates()
        assert test_plugin.plugin_id in updates
        assert updates[test_plugin.plugin_id] == "2.0.0"

def test_plugin_api_endpoints(plugin_manager):
    """Test plugin API endpoint registration"""
    test_plugin = TestPlugin()
    
    # Mock API endpoints
    test_plugin.get_api_endpoints = Mock(return_value={
        "/test": {
            "get": lambda: {"status": "ok"}
        }
    })
    
    plugin_manager.install_plugin(test_plugin)
    
    # Test endpoint registration
    endpoints = plugin_manager.get_plugin_endpoints(test_plugin.plugin_id)
    assert "/test" in endpoints
    assert "get" in endpoints["/test"]

def test_plugin_web_routes(plugin_manager):
    """Test plugin web route registration"""
    test_plugin = TestPlugin()
    
    # Mock web routes
    test_plugin.get_web_routes = Mock(return_value={
        "/test": "test_template.html"
    })
    
    plugin_manager.install_plugin(test_plugin)
    
    # Test route registration
    routes = plugin_manager.get_plugin_routes(test_plugin.plugin_id)
    assert "/test" in routes
    assert routes["/test"] == "test_template.html"

def test_plugin_cleanup(plugin_manager):
    """Test plugin cleanup and uninstallation"""
    test_plugin = TestPlugin()
    plugin_manager.install_plugin(test_plugin)
    
    # Test plugin disable
    assert plugin_manager.disable_plugin(test_plugin.plugin_id)
    assert not plugin_manager.is_plugin_enabled(test_plugin.plugin_id)
    
    # Test plugin uninstall
    assert plugin_manager.uninstall_plugin(test_plugin.plugin_id)
    assert test_plugin.plugin_id not in plugin_manager.get_installed_plugins()
