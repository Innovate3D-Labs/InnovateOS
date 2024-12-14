from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin):
    def __init__(self, id, username, email, role='user', created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.created_at = created_at or datetime.utcnow()
        self._password = None

    @property
    def password(self):
        raise AttributeError('Passwort kann nicht ausgelesen werden')

    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self._password, password)

    def has_permission(self, permission):
        permissions = {
            'user': ['view'],
            'operator': ['view', 'print', 'manage_printers'],
            'admin': ['view', 'print', 'manage_printers', 'manage_users', 'manage_system']
        }
        return permission in permissions.get(self.role, [])
