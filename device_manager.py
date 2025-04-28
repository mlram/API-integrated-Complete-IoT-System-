import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceManager:
    def __init__(self, mongo_handler, mqtt_handler):
        """
        Initialize device manager
        
        Args:
            mongo_handler: MongoDB handler for device storage
            mqtt_handler: MQTT handler for device communication
        """
        # Handle the case where handlers might be None
        self.mongo_handler = mongo_handler
        self.mqtt_handler = mqtt_handler
        
        # Initialize connection statuses
        self.has_mongo = self.mongo_handler is not None and hasattr(self.mongo_handler, 'is_connected')
        self.has_mqtt = self.mqtt_handler is not None and hasattr(self.mqtt_handler, 'publish_message')
        
        # Demo devices for when MongoDB is not available
        self.demo_devices = [
            {
                "device_id": "demo-temp-sensor-1",
                "name": "Demo Temperature Sensor 1",
                "device_type": "Temperature Sensor",
                "location": "Living Room",
                "last_seen": datetime.now().isoformat()
            },
            {
                "device_id": "demo-temp-sensor-2",
                "name": "Demo Temperature Sensor 2",
                "device_type": "Temperature Sensor",
                "location": "Bedroom",
                "last_seen": datetime.now().isoformat()
            },
            {
                "device_id": "demo-humid-sensor-1",
                "name": "Demo Humidity Sensor 1",
                "device_type": "Humidity Sensor",
                "location": "Kitchen",
                "last_seen": datetime.now().isoformat()
            }
        ]
        
        # Local device storage is managed centrally by the MongoDB handler
        # For now, we'll let the mongo_handler handle fallback to local storage
        # This keeps our code simpler and more maintainable
    
    def add_device(self, device_id, name, device_type=None, location=None, project_id=None):
        """
        Add a new device
        
        Args:
            device_id (str): Device ID
            name (str): Device name
            device_type (str): Device type
            location (str): Device location
            project_id (str): Project ID this device belongs to
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if MongoDB is available
        if not self.has_mongo:
            logger.warning("MongoDB not available, can't add device")
            return False
            
        # Add device to MongoDB
        result = self.mongo_handler.add_device(
            device_id=device_id,
            name=name,
            device_type=device_type,
            location=location,
            project_id=project_id
        )
        
        if result and self.has_mqtt:
            try:
                # Subscribe to device topics
                if hasattr(self.mqtt_handler, 'subscribe_to_topic'):
                    self.mqtt_handler.subscribe_to_topic(f"devices/{device_id}/#")
                
                # Publish welcome message
                welcome_topic = f"devices/{device_id}/control"
                welcome_message = {
                    "action": "welcome",
                    "message": f"Welcome to IoT Platform, {name}!",
                    "timestamp": time.time()
                }
                self.mqtt_handler.publish_message(welcome_topic, welcome_message)
            except Exception as e:
                logger.error(f"MQTT error while adding device: {e}")
                # Don't return False, as the device was still added to MongoDB
        
        return result
    
    def get_devices(self):
        """
        Get all devices
        
        Returns:
            list: List of device documents
        """
        # If MongoDB is not connected, return demo devices
        if not hasattr(self.mongo_handler, 'is_connected') or not self.mongo_handler.is_connected():
            return self.demo_devices
        
        # Otherwise get devices from MongoDB
        devices = self.mongo_handler.get_devices()
        
        # If no devices in MongoDB, return demo devices
        if not devices:
            return self.demo_devices
            
        return devices
    
    def get_device(self, device_id):
        """
        Get a device by ID
        
        Args:
            device_id (str): Device ID
            
        Returns:
            dict: Device document
        """
        # Handle demo devices
        if device_id.startswith('demo-'):
            for device in self.demo_devices:
                if device['device_id'] == device_id:
                    # Update last seen timestamp
                    device['last_seen'] = datetime.now().isoformat()
                    return device
        
        # If MongoDB is not connected, return None or demo device
        if not hasattr(self.mongo_handler, 'is_connected') or not self.mongo_handler.is_connected():
            # Check if it's a demo device
            for device in self.demo_devices:
                if device['device_id'] == device_id:
                    return device
            return None
        
        # Otherwise get device from MongoDB
        return self.mongo_handler.get_device(device_id)
    
    def remove_device(self, device_id):
        """
        Remove a device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if MongoDB is available
        if not self.has_mongo:
            logger.warning("MongoDB not available, can't remove device")
            return False
            
        # Handle demo devices - pretend to delete them but they'll come back
        if device_id.startswith('demo-'):
            logger.info(f"Simulating removal of demo device {device_id}")
            return True
            
        # Remove device from MongoDB
        result = self.mongo_handler.remove_device(device_id)
        
        if result and self.has_mqtt:
            try:
                # Unsubscribe from device topics
                if hasattr(self.mqtt_handler, 'unsubscribe_from_topic'):
                    self.mqtt_handler.unsubscribe_from_topic(f"devices/{device_id}/#")
                
                # Publish goodbye message
                goodbye_topic = f"devices/{device_id}/control"
                goodbye_message = {
                    "action": "goodbye",
                    "message": "Device removed from platform",
                    "timestamp": time.time()
                }
                self.mqtt_handler.publish_message(goodbye_topic, goodbye_message)
            except Exception as e:
                logger.error(f"MQTT error while removing device: {e}")
                # Don't return False, as the device was still removed from MongoDB
        
        return result
    
    def send_command(self, device_id, command, payload=None):
        """
        Send a command to a device
        
        Args:
            device_id (str): Device ID
            command (str): Command name
            payload: Command payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create command message
        command_topic = f"devices/{device_id}/command"
        command_message = {
            "command": command,
            "payload": payload,
            "timestamp": time.time()
        }
        
        # Publish command
        return self.mqtt_handler.publish_message(command_topic, command_message)
    
    def get_device_status(self, device_id):
        """
        Get device status
        
        Args:
            device_id (str): Device ID
            
        Returns:
            str: Device status ('Online' or 'Offline')
        """
        return self.mqtt_handler.get_device_status(device_id)
    
    def restart_device(self, device_id):
        """
        Send restart command to device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.send_command(device_id, "restart")
    
    def update_device(self, device_id, updates):
        """
        Update device settings
        
        Args:
            device_id (str): Device ID
            updates (dict): Device updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Update device in MongoDB
        if not self.mongo_handler.is_connected():
            logger.error("Not connected to MongoDB")
            return False
        
        try:
            # Update device
            result = self.mongo_handler.db.devices.update_one(
                {'device_id': device_id},
                {'$set': updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated device {device_id}")
                return True
            else:
                logger.warning(f"Device {device_id} not found or no changes made")
                return False
        except Exception as e:
            logger.error(f"Failed to update device: {e}")
            return False
