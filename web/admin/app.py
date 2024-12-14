from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_socketio import SocketIO
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from models.user import User
from models.printer import Printer, PrintJob
from events import init_socket_events

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
socketio = SocketIO(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Mock database (replace with real database in production)
users = {}
printers = {}
print_jobs = {}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = next((u for u in users.values() if u.username == username), None)
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if any(u.username == username for u in users.values()):
            flash('Username already exists')
            return render_template('auth/register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        users[user.id] = user
        
        login_user(user)
        return redirect(url_for('index'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/printers')
@login_required
def printers_page():
    return render_template('printers.html')

@app.route('/backups')
@login_required
def backups():
    return render_template('backups.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# API routes for printer management
@app.route('/api/printers', methods=['GET'])
@login_required
def get_printers():
    return jsonify({'printers': [p.to_dict() for p in printers.values()]})

@app.route('/api/printers', methods=['POST'])
@login_required
def add_printer():
    data = request.json
    printer = Printer(
        id=len(printers) + 1,
        name=data['name'],
        model=data.get('model')
    )
    printers[printer.id] = printer
    return jsonify(printer.to_dict()), 201

@app.route('/api/printers/<int:printer_id>', methods=['DELETE'])
@login_required
def remove_printer(printer_id):
    if printer_id in printers:
        del printers[printer_id]
        return '', 204
    return jsonify({'error': 'Printer not found'}), 404

# Initialize WebSocket events
init_socket_events(socketio)

if __name__ == '__main__':
    # Add a test user
    test_user = User(username='admin', email='admin@example.com')
    test_user.set_password('admin')
    users[test_user.id] = test_user
    
    # Add a test printer
    test_printer = Printer(id=1, name='Test Printer', model='Prusa i3 MK3S+')
    printers[test_printer.id] = test_printer
    
    socketio.run(app, debug=True)
