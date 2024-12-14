import os
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from werkzeug.security import generate_password_hash, check_password_hash

@dataclass
class UserRole:
    name: str
    permissions: List[str]
    description: str

@dataclass
class APIKey:
    key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    permissions: List[str]

@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    roles: List[str]
    api_keys: List[APIKey]
    two_factor_enabled: bool
    two_factor_secret: Optional[str]
    last_login: Optional[datetime]
    created_at: datetime
    is_active: bool

class UserManager:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.users_file = os.path.join(config_dir, "users.json")
        self.roles_file = os.path.join(config_dir, "roles.json")
        self.logger = logging.getLogger("UserManager")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize storage
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, UserRole] = {}
        
        # Load existing data
        self.load_roles()
        self.load_users()
        
        # Create default roles if they don't exist
        self.create_default_roles()

    def load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                data = json.load(f)
                for user_data in data.values():
                    # Convert datetime strings to datetime objects
                    user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
                    user_data['last_login'] = (datetime.fromisoformat(user_data['last_login']) 
                                             if user_data['last_login'] else None)
                    
                    # Convert API key data
                    api_keys = []
                    for key_data in user_data['api_keys']:
                        key_data['created_at'] = datetime.fromisoformat(key_data['created_at'])
                        key_data['expires_at'] = (datetime.fromisoformat(key_data['expires_at'])
                                                if key_data['expires_at'] else None)
                        api_keys.append(APIKey(**key_data))
                    user_data['api_keys'] = api_keys
                    
                    self.users[user_data['id']] = User(**user_data)

    def load_roles(self):
        """Load roles from JSON file"""
        if os.path.exists(self.roles_file):
            with open(self.roles_file, 'r') as f:
                data = json.load(f)
                self.roles = {name: UserRole(**role_data) 
                            for name, role_data in data.items()}

    def save_users(self):
        """Save users to JSON file"""
        data = {}
        for user_id, user in self.users.items():
            user_dict = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'roles': user.roles,
                'api_keys': [{
                    'key': key.key,
                    'name': key.name,
                    'created_at': key.created_at.isoformat(),
                    'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                    'permissions': key.permissions
                } for key in user.api_keys],
                'two_factor_enabled': user.two_factor_enabled,
                'two_factor_secret': user.two_factor_secret,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat(),
                'is_active': user.is_active
            }
            data[user_id] = user_dict
            
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=4)

    def save_roles(self):
        """Save roles to JSON file"""
        data = {name: {
            'name': role.name,
            'permissions': role.permissions,
            'description': role.description
        } for name, role in self.roles.items()}
        
        with open(self.roles_file, 'w') as f:
            json.dump(data, f, indent=4)

    def create_default_roles(self):
        """Create default user roles"""
        default_roles = {
            'admin': UserRole(
                name='admin',
                permissions=['*'],  # All permissions
                description='Administrator with full access'
            ),
            'operator': UserRole(
                name='operator',
                permissions=[
                    'printer.view', 'printer.control',
                    'backup.view', 'backup.create',
                    'system.view'
                ],
                description='Operator with printer control access'
            ),
            'user': UserRole(
                name='user',
                permissions=['printer.view', 'system.view'],
                description='Basic user with view access'
            )
        }
        
        for role_name, role in default_roles.items():
            if role_name not in self.roles:
                self.roles[role_name] = role
        
        self.save_roles()

    def create_user(self, username: str, email: str, password: str, roles: List[str] = None) -> Optional[User]:
        """Create a new user"""
        try:
            # Validate roles
            if roles is None:
                roles = ['user']
            for role in roles:
                if role not in self.roles:
                    raise ValueError(f"Invalid role: {role}")
            
            # Check if username or email already exists
            if any(u.username == username for u in self.users.values()):
                raise ValueError("Username already exists")
            if any(u.email == email for u in self.users.values()):
                raise ValueError("Email already exists")
            
            user = User(
                id=secrets.token_urlsafe(16),
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                roles=roles,
                api_keys=[],
                two_factor_enabled=False,
                two_factor_secret=None,
                last_login=None,
                created_at=datetime.now(),
                is_active=True
            )
            
            self.users[user.id] = user
            self.save_users()
            return user
            
        except Exception as e:
            self.logger.error(f"Failed to create user {username}: {str(e)}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = next((u for u in self.users.values() if u.username == username), None)
        if user and user.is_active and check_password_hash(user.password_hash, password):
            user.last_login = datetime.now()
            self.save_users()
            return user
        return None

    def authenticate_api_key(self, api_key: str) -> Optional[tuple[User, APIKey]]:
        """Authenticate a user with API key"""
        for user in self.users.values():
            for key in user.api_keys:
                if key.key == api_key:
                    if key.expires_at and key.expires_at < datetime.now():
                        continue
                    return user, key
        return None

    def create_api_key(self, user_id: str, name: str, permissions: List[str] = None,
                      expires_in_days: Optional[int] = None) -> Optional[APIKey]:
        """Create a new API key for a user"""
        try:
            user = self.users.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            api_key = APIKey(
                key=secrets.token_urlsafe(32),
                name=name,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
                permissions=permissions or []
            )
            
            user.api_keys.append(api_key)
            self.save_users()
            return api_key
            
        except Exception as e:
            self.logger.error(f"Failed to create API key for user {user_id}: {str(e)}")
            return None

    def revoke_api_key(self, user_id: str, api_key: str) -> bool:
        """Revoke an API key"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            user.api_keys = [k for k in user.api_keys if k.key != api_key]
            self.save_users()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revoke API key for user {user_id}: {str(e)}")
            return False

    def enable_two_factor(self, user_id: str, secret: str) -> bool:
        """Enable two-factor authentication for a user"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            user.two_factor_enabled = True
            user.two_factor_secret = secret
            self.save_users()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable 2FA for user {user_id}: {str(e)}")
            return False

    def disable_two_factor(self, user_id: str) -> bool:
        """Disable two-factor authentication for a user"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            user.two_factor_enabled = False
            user.two_factor_secret = None
            self.save_users()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable 2FA for user {user_id}: {str(e)}")
            return False

    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user information"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            # Update allowed fields
            allowed_fields = ['email', 'roles', 'is_active']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            
            self.save_users()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user {user_id}: {str(e)}")
            return False

    def change_password(self, user_id: str, new_password: str) -> bool:
        """Change a user's password"""
        try:
            user = self.users.get(user_id)
            if not user:
                return False
            
            user.password_hash = generate_password_hash(new_password)
            self.save_users()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to change password for user {user_id}: {str(e)}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        try:
            if user_id in self.users:
                del self.users[user_id]
                self.save_users()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete user {user_id}: {str(e)}")
            return False

    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user based on their roles"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        permissions = set()
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if role:
                if '*' in role.permissions:
                    return ['*']  # User has all permissions
                permissions.update(role.permissions)
        
        return list(permissions)

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission"""
        permissions = self.get_user_permissions(user_id)
        return '*' in permissions or permission in permissions

if __name__ == "__main__":
    manager = UserManager("/etc/innovate/users")
    
    # Beispiel: Erstelle Admin-Benutzer
    if manager.create_user("admin", "admin@example.com", "admin123", ["admin"]):
        print("Admin-Benutzer erstellt")
        
    # Liste alle Benutzer
    print("Benutzer:", list(manager.users.values()))
