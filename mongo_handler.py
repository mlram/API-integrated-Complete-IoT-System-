import pymongo
import logging
import time
import hashlib
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBHandler:
    def __init__(self, connection_string, db_name):
        """
        Initialize MongoDB client

        Args:
            connection_string (str): MongoDB connection string
            db_name (str): Database name
        """
        self.connection_string = connection_string
        self.db_name = db_name

        # Initialize client
        try:
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[db_name]

            # Create collections if they don't exist
            if 'users' not in self.db.list_collection_names():
                self.db.create_collection('users')
            if 'devices' not in self.db.list_collection_names():
                self.db.create_collection('devices')
            if 'projects' not in self.db.list_collection_names():
                self.db.create_collection('projects')

            # Verify connection
            self.client.admin.command('ping')
            logger.info(
                f"Connected to MongoDB at {connection_string}, database: {db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None

    def is_connected(self):
        """
        Check if connected to MongoDB

        Returns:
            bool: True if connected, False otherwise
        """
        return self.client is not None and self.db is not None

    def hash_password(self, password):
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

    def verify_password(self, stored_salt, stored_key, password):
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

    def add_user(self, username, password, role='User'):
        """
        Add a user to the database

        Args:
            username (str): Username
            password (str): Password
            role (str): User role (Admin, User, Guest)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Check if user already exists
            if self.db.users.find_one({'username': username}):
                logger.warning(f"User {username} already exists")
                return False

            # Hash password
            salt, hashed_password = self.hash_password(password)

            # Create user document
            user = {
                'username': username,
                'salt': salt,
                'hashed_password': hashed_password,
                'role': role,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Insert user
            result = self.db.users.insert_one(user)
            logger.info(f"Added user {username} with ID {result.inserted_id}")
            return True
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
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return None

        try:
            # Find user
            user = self.db.users.find_one({'username': username})
            if not user:
                logger.warning(f"User {username} not found")
                return None

            # Verify password
            if self.verify_password(user['salt'], user['hashed_password'], password):
                # Remove sensitive data before returning
                user.pop('salt', None)
                user.pop('hashed_password', None)
                return user
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
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return []

        try:
            # Find all users
            users = list(self.db.users.find(
                {}, {'salt': 0, 'hashed_password': 0}))

            # Convert ObjectId to string for JSON serialization
            for user in users:
                if '_id' in user:
                    user['_id'] = str(user['_id'])

            return users
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []

    def remove_user(self, username):
        """
        Remove a user from the database

        Args:
            username (str): Username

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Delete user
            result = self.db.users.delete_one({'username': username})
            if result.deleted_count > 0:
                logger.info(f"Removed user {username}")
                return True
            else:
                logger.warning(f"User {username} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove user: {e}")
            return False

    def add_device(self, device_id, name, device_type=None, location=None, project_id=None):
        """
        Add a device to the database

        Args:
            device_id (str): Device ID
            name (str): Device name
            device_type (str): Device type
            location (str): Device location
            project_id (str): Project ID this device belongs to

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Check if device already exists
            if self.db.devices.find_one({'device_id': device_id}):
                logger.warning(f"Device {device_id} already exists")
                return False

            # If project_id is provided, check if it exists
            if project_id and not self.db.projects.find_one({'project_id': project_id}):
                logger.warning(f"Project {project_id} does not exist")
                return False

            # Create device document
            device = {
                'device_id': device_id,
                'name': name,
                'device_type': device_type,
                'location': location,
                'project_id': project_id,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_seen': None,
                'status': 'Offline'
            }

            # Insert device
            result = self.db.devices.insert_one(device)
            logger.info(
                f"Added device {device_id} with ID {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add device: {e}")
            return False

    def get_devices(self):
        """
        Get all devices

        Returns:
            list: List of device documents
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return []

        try:
            # Find all devices
            devices = list(self.db.devices.find({}))
            # Convert ObjectId to string for JSON serialization
            for device in devices:
                if '_id' in device:
                    device['_id'] = str(device['_id'])
            return devices
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            return []

    def get_device(self, device_id):
        """
        Get a device by ID

        Args:
            device_id (str): Device ID

        Returns:
            dict: Device document
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return None

        try:
            # Find device
            device = self.db.devices.find_one({'device_id': device_id})
            # Convert ObjectId to string for JSON serialization
            if device and '_id' in device:
                device['_id'] = str(device['_id'])
            return device
        except Exception as e:
            logger.error(f"Failed to get device: {e}")
            return None

    def update_device_last_seen(self, device_id):
        """
        Update device last seen timestamp

        Args:
            device_id (str): Device ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Update device
            result = self.db.devices.update_one(
                {'device_id': device_id},
                {'$set': {'last_seen': time.time()}}
            )

            if result.modified_count > 0:
                return True
            else:
                logger.warning(f"Device {device_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to update device last seen: {e}")
            return False

    def update_device_status(self, device_id, status):
        """
        Update device status

        Args:
            device_id (str): Device ID
            status (str): New status ('Online' or 'Offline')

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Update device
            result = self.db.devices.update_one(
                {'device_id': device_id},
                {'$set': {'status': status}}
            )

            if result.modified_count > 0:
                logger.info(f"Updated device {device_id} status to {status}")
                return True
            else:
                logger.warning(f"Device {device_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            return False

    def remove_device(self, device_id):
        """
        Remove a device from the database

        Args:
            device_id (str): Device ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Delete device
            result = self.db.devices.delete_one({'device_id': device_id})
            if result.deleted_count > 0:
                logger.info(f"Removed device {device_id}")
                return True
            else:
                logger.warning(f"Device {device_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove device: {e}")
            return False

    def create_project(self, project_id, name, owner, description=None):
        """
        Create a new project

        Args:
            project_id (str): Project ID
            name (str): Project name
            owner (str): Username of the project owner
            description (str): Project description

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Check if project already exists
            if self.db.projects.find_one({'project_id': project_id}):
                logger.warning(f"Project {project_id} already exists")
                return False

            # Create project document
            project = {
                'project_id': project_id,
                'name': name,
                'description': description,
                'owner': owner,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Insert project
            result = self.db.projects.insert_one(project)
            logger.info(f"Added project {name} with ID {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return False

    def get_projects(self, owner=None):
        """
        Get all projects, optionally filtered by owner

        Args:
            owner (str): Username of the project owner

        Returns:
            list: List of project documents
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return []

        try:
            # Find projects, optionally filtered by owner
            filter_dict = {}
            if owner:
                filter_dict['owner'] = owner

            projects = list(self.db.projects.find(filter_dict))

            # Convert ObjectId to string for JSON serialization
            for project in projects:
                if '_id' in project:
                    project['_id'] = str(project['_id'])

            return projects
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []

    def get_project(self, project_id):
        """
        Get a project by ID

        Args:
            project_id (str): Project ID

        Returns:
            dict: Project document
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return None

        try:
            # Find project
            project = self.db.projects.find_one({'project_id': project_id})

            if project and '_id' in project:
                project['_id'] = str(project['_id'])

            return project
        except Exception as e:
            logger.error(f"Failed to get project: {e}")
            return None

    def remove_project(self, project_id):
        """
        Remove a project from the database

        Args:
            project_id (str): Project ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to MongoDB")
            return False

        try:
            # Delete project
            result = self.db.projects.delete_one({'project_id': project_id})

            if result.deleted_count > 0:
                logger.info(f"Removed project {project_id}")

                self.db.devices.update_many(
                    {'project_id': project_id},
                    {'$set': {'project_id': None}}
                )

                return True
            else:
                logger.warning(f"Project {project_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove project: {e}")
            return False
