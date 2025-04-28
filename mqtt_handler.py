"""
MQTT Handler for IoT Platform

Manages connections to MQTT broker and processes device messages
"""
import os
import paho.mqtt.client as mqtt
import json
import logging
import time
from datetime import datetime
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTHandler:
    def __init__(self, broker, port, username=None, password=None):
        """
        Initialize MQTT client

        Args:
            broker (str): MQTT broker address
            port (int): MQTT broker port
            username (str): MQTT username
            password (str): MQTT password
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.connected = False
        self.callbacks = []

        # Initialize client
        self.client_id = f"iot-platform-{os.getpid()}"
        self.client = mqtt.Client(client_id=self.client_id)

        if username and password:
            self.client.username_pw_set(username, password)

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Connection retry settings
        self.retry_interval = 5
        self.max_retries = 12  # 1 minute of retries
        self.retry_count = 0
        self.retry_thread = None

        # Connect
        self._connect()

    def is_connected(self):
        """
        Check if connected to MQTT broker

        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected

    def _connect(self):
        """Connect to MQTT broker with retry logic"""
        try:
            logger.info(
                f"Connecting to MQTT broker at {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self._schedule_reconnect()

    def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self.retry_count < self.max_retries:
            logger.info(
                f"Scheduling reconnection attempt ({self.retry_count + 1}/{self.max_retries})...")
            self.retry_count += 1
            if self.retry_thread is not None and self.retry_thread.is_alive():
                return
            self.retry_thread = threading.Timer(
                self.retry_interval, self._connect)
            self.retry_thread.daemon = True
            self.retry_thread.start()
        else:
            logger.error("Maximum reconnection attempts reached")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            self.retry_count = 0

            # Subscribe to device topics
            client.subscribe("devices/+/data/#")
            logger.info("Subscribed to device data topics")
        else:
            logger.error(f"Failed to connect with code {rc}")
            self.connected = False
            self._schedule_reconnect()

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        logger.warning(f"Disconnected from MQTT broker with code {rc}")
        self.connected = False

        # Attempt to reconnect if not requested by client
        if rc != 0:
            self._schedule_reconnect()

    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker"""
        try:
            logger.debug(f"Received message on topic: {msg.topic}")

            # Extract device ID and measurement from topic
            # Expected format: devices/<device_id>/data/<measurement>
            parts = msg.topic.split('/')
            if len(parts) >= 4:
                device_id = parts[1]
                measurement = parts[3]

                # Parse payload
                try:
                    payload = json.loads(msg.payload.decode())
                except json.JSONDecodeError:
                    # Handle non-JSON payloads
                    payload = {'value': msg.payload.decode()}

                # Call registered callbacks
                for callback in self.callbacks:
                    callback(device_id, measurement, payload)
            else:
                logger.warning(f"Invalid topic format: {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def register_callback(self, callback):
        """
        Register a callback for incoming messages

        Args:
            callback: Function to call with (device_id, measurement, payload)
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def publish(self, topic, payload, qos=0, retain=False):
        """
        Publish a message to the broker

        Args:
            topic (str): Topic to publish to
            payload (dict or str): Message payload
            qos (int): QoS level
            retain (bool): Whether to retain the message

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False

        try:

            if isinstance(payload, dict):
                payload = json.dumps(payload)

            # Publish message
            result = self.client.publish(topic, payload, qos, retain)

            # Check if successful
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published message to {topic}")
                return True
            else:
                logger.error(f"Failed to publish message: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

    def send_command(self, device_id, command, payload=None):
        """
        Send a command to a device

        Args:
            device_id (str): Device ID
            command (str): Command name
            payload (dict): Command payload

        Returns:
            bool: True if successful, False otherwise
        """
        # Command topic: devices/<device_id>/commands/<command>
        topic = f"devices/{device_id}/commands/{command}"

        # Default empty payload
        if payload is None:
            payload = {}

        # Add timestamp to payload
        payload['timestamp'] = datetime.now().isoformat()

        # Publish command
        return self.publish(topic, payload)

    def close(self):
        """Close connection to broker"""
        if self.retry_thread is not None and self.retry_thread.is_alive():
            self.retry_thread.cancel()
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
