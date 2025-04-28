"""
Local authentication for when MongoDB is not available
"""
import hashlib
import os
import logging
import json
from datetime import datetime
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default users file
USERS_FILE = "users.json"

def hash_password(password):
    """
    Hash a password with a salt
    
    Args:
        password (str): Password to hash
        
    Returns:
        tuple: (salt, hashed_password)
    """
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex(), key.hex()

def verify_password(stored_salt, stored_key, password):
    """
    Verify a password against a stored hash
    
    Args:
        stored_salt (str): Stored salt (hex)
        stored_key (str): Stored key (hex)
        password (str): Password to verify
        
    Returns:
        bool: True if password matches, False otherwise
    """
    salt = bytes.fromhex(stored_salt)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return key.hex() == stored_key

class LocalAuthHandler:
    def __init__(self, users_file=USERS_FILE):
        """
        Initialize local authentication handler
        
        Args:
            users_file (str): Path to users JSON file
        """
        self.users_file = users_file
        self.users = self._load_users()
        
        # Create default admin user if no users exist
        if not self.users:
            self._create_default_admin()
    
    def _load_users(self):
        """
        Load users from file
        
        Returns:
            list: List of user documents
        """
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Failed to load users from file: {e}")
            return []
    
    def _save_users(self):
        """
        Save users to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save users to file: {e}")
            return False
    
    def _create_default_admin(self):
        """
        Create default admin user
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.add_user('admin', 'admin123', 'Admin')
    
    def is_connected(self):
        """
        Check if local auth is available
        
        Returns:
            bool: True if available, False otherwise
        """
        return True
    
    def add_user(self, username, password, role='User'):
        """
        Add a user
        
        Args:
            username (str): Username
            password (str): Password
            role (str): User role (Admin, User, Guest)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if user already exists
            if any(user.get('username') == username for user in self.users):
                logger.warning(f"User {username} already exists")
                return False
            
            # Hash password
            salt, hashed_password = hash_password(password)
            
            # Create user document
            user = {
                'username': username,
                'salt': salt,
                'hashed_password': hashed_password,
                'role': role,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add user
            self.users.append(user)
            
            # Save users
            if self._save_users():
                logger.info(f"Added user {username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add user: {e}")
            return False
    
    def verify_user(self, username, password):
        """
        Verify user credentials
        
        Args:
            username (str): Username
            password (str): Password
            
        Returns:
            dict: User document if valid, None otherwise
        """
        try:
            # Find user
            user = next((u for u in self.users if u.get('username') == username), None)
            if not user:
                logger.warning(f"User {username} not found")
                return None
            
            # Verify password
            if verify_password(user['salt'], user['hashed_password'], password):
                # Return user without sensitive data
                user_copy = user.copy()
                user_copy.pop('salt', None)
                user_copy.pop('hashed_password', None)
                return user_copy
            else:
                logger.warning(f"Invalid password for user {username}")
                return None
        except Exception as e:
            logger.error(f"Failed to verify user: {e}")
            return None
    
    def get_users(self):
        """
        Get all users
        
        Returns:
            list: List of user documents
        """
        try:
            # Return users without sensitive data
            return [{k: v for k, v in user.items() if k not in ['salt', 'hashed_password']} 
                   for user in self.users]
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []
    
    def remove_user(self, username):
        """
        Remove a user
        
        Args:
            username (str): Username
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find user
            index = next((i for i, u in enumerate(self.users) 
                          if u.get('username') == username), -1)
            if index == -1:
                logger.warning(f"User {username} not found")
                return False
            
            # Remove user
            self.users.pop(index)
            
            # Save users
            if self._save_users():
                logger.info(f"Removed user {username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove user: {e}")
            return False

# For direct usage
local_auth = LocalAuthHandler()