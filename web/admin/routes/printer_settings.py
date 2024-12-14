from flask import Blueprint, render_template, jsonify
from flask_socketio import emit
from system.printer.printer_manager import PrinterManager

printer_settings = Blueprint('printer_settings', __name__)
socketio = None

def init_socketio(socket):
    global socketio
    socketio = socket

@printer_settings.route('/printer')
def printer_settings_page():
    printer = PrinterManager.get_current_printer()
    return render_template('settings/printer.html', printer=printer)

@socketio.on('save_printer_config')
def handle_printer_config(data):
    try:
        PrinterManager.update_printer_config(data)
        emit('printer_status', {'status': 'success'})
    except Exception as e:
        emit('printer_status', {'status': 'error', 'message': str(e)})

@socketio.on('level_point')
def handle_level_point(data):
    try:
        PrinterManager.move_to_level_point(data['point'])
        emit('printer_status', {'status': 'success'})
    except Exception as e:
        emit('printer_status', {'status': 'error', 'message': str(e)})

@socketio.on('auto_level')
def handle_auto_level():
    try:
        PrinterManager.start_auto_leveling()
        emit('printer_status', {'status': 'success'})
    except Exception as e:
        emit('printer_status', {'status': 'error', 'message': str(e)})

@socketio.on('save_calibration')
def handle_calibration(data):
    try:
        PrinterManager.update_calibration(data)
        emit('printer_status', {'status': 'success'})
    except Exception as e:
        emit('printer_status', {'status': 'error', 'message': str(e)})

@socketio.on('save_temp_profiles')
def handle_temp_profiles(data):
    try:
        PrinterManager.update_temp_profiles(data['profiles'])
        emit('printer_status', {'status': 'success'})
    except Exception as e:
        emit('printer_status', {'status': 'error', 'message': str(e)})

@socketio.on('save_safety_settings')
def handle_safety_settings(data):
    try:
        PrinterManager.update_safety_settings(data)
        emit('printer_status', {'status': 'success'})
    except Exception as e:
        emit('printer_status', {'status': 'error', 'message': str(e)})
