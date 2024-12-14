from flask import Blueprint, render_template, jsonify
from flask_socketio import emit
import psutil
import time
from system.update.system_updater import SystemUpdater
from system.plugins.plugin_manager import PluginManager
from system.backup.backup_manager import BackupManager

settings = Blueprint('settings', __name__)
socketio = None

def init_socketio(socket):
    global socketio
    socketio = socket

@settings.route('/system')
def system_settings():
    system_info = {
        'version': SystemUpdater.get_current_version(),
        'update_channel': SystemUpdater.get_update_channel(),
        'auto_check': SystemUpdater.get_auto_check(),
        'auto_download': SystemUpdater.get_auto_download(),
        'auto_install': SystemUpdater.get_auto_install(),
        'auto_backup': BackupManager.get_auto_backup_enabled()
    }
    return render_template('settings/system.html', system=system_info)

@socketio.on('set_update_channel')
def handle_update_channel(data):
    SystemUpdater.set_update_channel(data['channel'])
    emit('update_status', {'status': f'Update-Kanal auf {data["channel"]} geändert'})

@socketio.on('set_auto_update')
def handle_auto_update(data):
    SystemUpdater.set_auto_check(data['auto_check'])
    SystemUpdater.set_auto_download(data['auto_download'])
    SystemUpdater.set_auto_install(data['auto_install'])

@socketio.on('check_updates')
def handle_check_updates():
    def update_progress(progress, status):
        emit('update_status', {
            'progress': progress,
            'status': status,
            'available_update': SystemUpdater.is_update_available()
        })

    SystemUpdater.check_updates(progress_callback=update_progress)

@socketio.on('install_update')
def handle_install_update():
    def update_progress(progress, status):
        emit('update_status', {
            'progress': progress,
            'status': status,
            'available_update': SystemUpdater.is_update_available()
        })

    SystemUpdater.install_update(progress_callback=update_progress)

@socketio.on('get_system_stats')
def handle_system_stats():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = psutil.boot_time()
    uptime = time.time() - boot_time

    emit('system_stats', {
        'cpu': cpu_percent,
        'memory': memory.percent,
        'disk': disk.percent,
        'uptime': uptime
    })

@socketio.on('set_auto_backup')
def handle_auto_backup(data):
    BackupManager.set_auto_backup(data['enabled'], data['interval'])

@socketio.on('create_backup')
def handle_create_backup():
    def backup_progress(progress, status):
        emit('backup_status', {
            'progress': progress,
            'status': status,
            'last_backup': BackupManager.get_last_backup_time(),
            'backups': BackupManager.get_available_backups()
        })

    BackupManager.create_backup(progress_callback=backup_progress)

@socketio.on('get_backup_status')
def handle_backup_status():
    emit('backup_status', {
        'last_backup': BackupManager.get_last_backup_time(),
        'backups': BackupManager.get_available_backups()
    })

@socketio.on('restore_backup')
def handle_restore_backup(data):
    def restore_progress(progress, status):
        emit('backup_status', {
            'progress': progress,
            'status': status,
            'last_backup': BackupManager.get_last_backup_time(),
            'backups': BackupManager.get_available_backups()
        })

    BackupManager.restore_backup(data['backup_id'], progress_callback=restore_progress)

@socketio.on('delete_backup')
def handle_delete_backup(data):
    BackupManager.delete_backup(data['backup_id'])
    emit('backup_status', {
        'last_backup': BackupManager.get_last_backup_time(),
        'backups': BackupManager.get_available_backups()
    })

@socketio.on('refresh_plugins')
def handle_refresh_plugins():
    PluginManager.refresh_plugins()
    emit('plugin_list', {
        'plugins': PluginManager.get_plugin_list()
    })

@socketio.on('get_plugin_list')
def handle_get_plugin_list():
    emit('plugin_list', {
        'plugins': PluginManager.get_plugin_list()
    })

@socketio.on('toggle_plugin')
def handle_toggle_plugin(data):
    if data['enabled']:
        PluginManager.enable_plugin(data['plugin_name'])
    else:
        PluginManager.disable_plugin(data['plugin_name'])
    emit('plugin_list', {
        'plugins': PluginManager.get_plugin_list()
    })

@socketio.on('update_plugin')
def handle_update_plugin(data):
    def update_progress(progress, status):
        emit('plugin_list', {
            'plugins': PluginManager.get_plugin_list(),
            'progress': progress,
            'status': status
        })

    PluginManager.update_plugin(data['plugin_name'], progress_callback=update_progress)
