import requests
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from settings import API_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIClient:
    """Simple client for interacting with the IoT Platform API"""

    def __init__(self, base_url=API_URL):
        """Initialize API client

        Args:
            base_url (str): Base URL of the API
        """
        # multiple base URLs
        self.base_urls = [
            "http://0.0.0.0:8000",        # Try local server binding first
            "http://localhost:8000",
            base_url,
            "http://127.0.0.1:8000",      # localhost IP
            "http://host.docker.internal:8000",  # Docker host
        ]
        self.last_checked = 0
        self.health_check_interval = 60
        self.base_url = self._find_working_url()
        self.token = None
        self.token_type = None
        self.headers = {}

    def _find_working_url(self):
        """Try multiple URLs and return the first one that works"""

        current_time = time.time()
        if (current_time - self.last_checked) < self.health_check_interval:
            return self.base_url

        self.last_checked = current_time

        if hasattr(self, 'base_url') and self.base_url:
            try:
                logger.info(f"Checking current API URL: {self.base_url}")
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    logger.info(f"Current API URL is working: {self.base_url}")
                    return self.base_url
            except Exception as e:
                logger.debug(f"Current API URL is not working: {e}")

        # Try all URLs in the list
        for url in self.base_urls:
            try:
                logger.info(f"Trying API URL: {url}")
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    logger.info(f"Successfully connected to API at {url}")
                    return url
            except Exception as e:
                logger.debug(f"Failed to connect to {url}: {e}")
                continue

        # If no URL works, return the first one as default
        logger.warning("Could not find working API URL, using default")
        return self.base_urls[0]

    def _update_auth_header(self):
        """Update authorization header with the token"""
        if self.token and self.token_type:
            self.headers["Authorization"] = f"{self.token_type} {self.token}"

    def login(self, username: str, password: str) -> bool:
        """Login to get access token

        Args:
            username (str): User's username
            password (str): User's password

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.token_type = data["token_type"]
                self._update_auth_header()
                return True
            else:
                logger.error(
                    f"Login failed with status code {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information

        Returns:
            dict: User information or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get user info: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)

        Returns:
            list: List of users or empty list if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get users: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return []

    def create_user(self, username: str, password: str, role: str = "User") -> bool:
        """Create a new user (admin only)

        Args:
            username (str): New user's username
            password (str): New user's password
            role (str): User role (Admin, User, Guest)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/users",
                json={"username": username, "password": password, "role": role},
                headers=self.headers
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to create user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def delete_user(self, username: str) -> bool:
        """Delete a user (admin only)

        Args:
            username (str): Username to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.base_url}/users/{username}",
                headers=self.headers
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to delete user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices

        Returns:
            list: List of devices or empty list if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/devices",
                headers=self.headers
            )

            if response.status_code == 200:
                # Add debug logging
                data = response.json()
                logger.info(f"Device API response: {data}")
                if isinstance(data, dict) and "data" in data:
                    # Proper format: {"success": true, "message": "...", "data": [...]}
                    return data.get("data", [])
                elif isinstance(data, list):
                    # Already a list format
                    return data
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return []
            else:
                logger.error(
                    f"Failed to get devices: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            return []

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific device by ID

        Args:
            device_id (str): Device ID

        Returns:
            dict: Device information or None if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/devices/{device_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get device: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to get device: {e}")
            return None

    def create_device(self, device_id: str, name: str, device_type: str = None, location: str = None, project_id: str = None) -> bool:
        """Create a new device

        Args:
            device_id (str): Device ID
            name (str): Device name
            device_type (str): Device type
            location (str): Device location
            project_id (str): Project ID this device belongs to

        Returns:
            bool: True if successful, False otherwise
        """
        payload = {
            "device_id": device_id,
            "name": name
        }

        if device_type:
            payload["device_type"] = device_type

        if location:
            payload["location"] = location

        if project_id:
            payload["project_id"] = project_id

        try:
            response = requests.post(
                f"{self.base_url}/devices",
                json=payload,
                headers=self.headers
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to create device: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to create device: {e}")
            return False

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """Update a device

        Args:
            device_id (str): Device ID
            updates (dict): Device updates

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.put(
                f"{self.base_url}/devices/{device_id}",
                json=updates,
                headers=self.headers
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to update device: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to update device: {e}")
            return False

    def delete_device(self, device_id: str) -> bool:
        """Delete a device

        Args:
            device_id (str): Device ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.base_url}/devices/{device_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to delete device: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete device: {e}")
            return False

    def send_command(self, device_id: str, command: str, payload: Dict[str, Any] = None) -> bool:
        """Send a command to a device

        Args:
            device_id (str): Device ID
            command (str): Command name
            payload (dict): Optional command payload

        Returns:
            bool: True if successful, False otherwise
        """
        cmd_payload = {
            "command": command,
            "payload": payload or {}
        }

        try:
            response = requests.post(
                f"{self.base_url}/devices/{device_id}/command",
                json=cmd_payload,
                headers=self.headers
            )

            if response.status_code == 200:
                return True
            else:
                logger.error(
                    f"Failed to send command: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False

    def get_device_data(
        self,
        device_id: str,
        start: Optional[Union[datetime, str]] = None,
        end: Optional[Union[datetime, str]] = None,
        measurement: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get data for a specific device

        Args:
            device_id (str): Device ID
            start (datetime or str): Start time for query
            end (datetime or str): End time for query
            measurement (str): Measurement name filter

        Returns:
            list: List of data points or empty list if failed
        """
        params = {}

        if start:
            if isinstance(start, datetime):
                params["start"] = start.isoformat()
            else:
                params["start"] = start

        if end:
            if isinstance(end, datetime):
                params["end"] = end.isoformat()
            else:
                params["end"] = end

        if measurement:
            params["measurement"] = measurement

        try:
            response = requests.get(
                f"{self.base_url}/data/{device_id}",
                params=params,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get device data: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Failed to get device data: {e}")
            return []

    def get_device_latest_data(self, device_id: str) -> Dict[str, Any]:
        """Get latest data for a specific device

        Args:
            device_id (str): Device ID

        Returns:
            dict: Latest data or empty dict if failed
        """
        try:
            response = requests.get(
                f"{self.base_url}/data/{device_id}/latest",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get latest data: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Failed to get latest data: {e}")
            return {}

    # -------------------------------------------------------------------------
    # Project Management
    # -------------------------------------------------------------------------

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects

        Returns:
            List[Dict[str, Any]]: List of projects
        """
        if not self.token:
            logger.warning("Not authenticated. Call login() first.")
            return []

        try:
            response = requests.get(
                f"{self.base_url}/projects",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            logger.error(
                f"Failed to get projects: {response.status_code} - {response.text}")
            return []
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID

        Args:
            project_id (str): Project ID

        Returns:
            Optional[Dict[str, Any]]: Project data or None if not found
        """
        if not self.token:
            logger.warning("Not authenticated. Call login() first.")
            return None

        try:
            response = requests.get(
                f"{self.base_url}/projects/{project_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            logger.error(
                f"Failed to get project: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None

    def create_project(self, project_id: str, name: str, description: str = None) -> bool:
        """Create a new project

        Args:
            project_id (str): Project ID
            name (str): Project name
            description (str, optional): Project description

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.token:
            logger.warning("Not authenticated. Call login() first.")
            return False

        payload = {
            "project_id": project_id,
            "name": name
        }

        if description:
            payload["description"] = description

        try:
            response = requests.post(
                f"{self.base_url}/projects",
                json=payload,
                headers=self.headers
            )
            if response.status_code == 200:
                return True
            logger.error(
                f"Failed to create project: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return False

    def delete_project(self, project_id: str) -> bool:
        """Delete a project

        Args:
            project_id (str): Project ID

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.token:
            logger.warning("Not authenticated. Call login() first.")
            return False

        try:
            response = requests.delete(
                f"{self.base_url}/projects/{project_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                return True
            logger.error(
                f"Failed to delete project: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return False

    def get_project_devices(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all devices for a project

        Args:
            project_id (str): Project ID

        Returns:
            List[Dict[str, Any]]: List of devices
        """
        if not self.token:
            logger.warning("Not authenticated. Call login() first.")
            return []

        try:
            response = requests.get(
                f"{self.base_url}/projects/{project_id}/devices",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            logger.error(
                f"Failed to get project devices: {response.status_code} - {response.text}")
            return []
        except Exception as e:
            logger.error(f"Error getting project devices: {e}")
            return []

    # -------------------------------------------------------------------------
    # Health check
    # -------------------------------------------------------------------------

    def check_health(self) -> Dict[str, Any]:
        """Check the health of the API and connected services

        Returns:
            dict: Health status information
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Health check failed: {response.status_code} - {response.text}")
                return {
                    "api": "error",
                    "mongodb": "unknown",
                    "influxdb": "unknown",
                    "mqtt": "unknown"
                }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "api": "error",
                "mongodb": "unknown",
                "influxdb": "unknown",
                "mqtt": "unknown"
            }

    def is_logged_in(self) -> bool:
        """Check if user is logged in

        Returns:
            bool: True if logged in, False otherwise
        """
        return self.token is not None
