#!/usr/bin/env python3
"""
Test script for verifying connections to MongoDB, InfluxDB and MQTT broker
Run this script to test if your settings are correctly configured
"""
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_mongodb_connection():
    """Test MongoDB connection"""
    logger.info("Testing MongoDB connection...")
    try:
        from settings import MONGODB_URI, MONGODB_DATABASE
        import pymongo

        client = pymongo.MongoClient(MONGODB_URI)
        db = client[MONGODB_DATABASE]

        # Verify connection with a simple command
        client.admin.command('ping')

        # List collections
        collections = db.list_collection_names()
        logger.info(f"Successfully connected to MongoDB at {MONGODB_URI}")
        logger.info(f"Available collections: {collections}")

        # Try to read users collection
        users = list(db.users.find())
        logger.info(f"Found {len(users)} users in the database")

        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return False


def test_influxdb_connection():
    """Test InfluxDB connection"""
    logger.info("Testing InfluxDB connection...")
    try:
        from settings import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET
        from influxdb_client import InfluxDBClient

        client = InfluxDBClient(
            url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        health = client.health()

        # Get the list of buckets to verify permissions
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets().buckets
        bucket_names = [bucket.name for bucket in buckets]

        logger.info(f"Successfully connected to InfluxDB at {INFLUXDB_URL}")
        logger.info(f"InfluxDB status: {health.status}")
        logger.info(f"Available buckets: {bucket_names}")

        # Check if our bucket exists
        if INFLUXDB_BUCKET in bucket_names:
            logger.info(f"Bucket {INFLUXDB_BUCKET} found")
        else:
            logger.warning(
                f"Bucket {INFLUXDB_BUCKET} not found. You may need to create it.")

        # Try to write a test point
        write_api = client.write_api()
        test_point = {
            "measurement": "test_measurement",
            "tags": {"source": "connection_test"},
            "fields": {"value": 1.0},
            "time": datetime.utcnow()
        }

        write_api.write(bucket=INFLUXDB_BUCKET, record=test_point)
        logger.info("Successfully wrote test data point to InfluxDB")

        return True
    except Exception as e:
        logger.error(f"Failed to connect to InfluxDB: {str(e)}")
        return False


def test_mqtt_connection():
    """Test MQTT broker connection"""
    logger.info("Testing MQTT broker connection...")
    try:
        from settings import MQTT_BROKER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD
        import paho.mqtt.client as mqtt
        import uuid
        import threading

        # Define callback functions
        connected_event = threading.Event()
        message_received_event = threading.Event()
        received_messages = []

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info(
                    f"Successfully connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
                connected_event.set()

                # Subscribe to test topic
                test_topic = f"test/iot_platform/{uuid.uuid4()}"
                client.subscribe(test_topic)
                logger.info(f"Subscribed to test topic: {test_topic}")

                # Publish a test message
                client.publish(test_topic, "Test message from IoT Platform")
                logger.info(f"Published test message to {test_topic}")
            else:
                logger.error(
                    f"Failed to connect to MQTT broker, return code: {rc}")

        def on_message(client, userdata, msg):
            message = f"Received message on topic {msg.topic}: {msg.payload.decode()}"
            logger.info(message)
            received_messages.append(message)
            message_received_event.set()

        # Set up client
        client_id = f"iot-platform-test-{uuid.uuid4()}"
        client = mqtt.Client(client_id=client_id)
        client.on_connect = on_connect
        client.on_message = on_message

        # Set username and password if provided
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        # Connect to broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        # Start the loop
        client.loop_start()

        # Wait for connection
        if connected_event.wait(timeout=5):
            # Wait for message
            if message_received_event.wait(timeout=5):
                logger.info("MQTT connection test successful")
                client.loop_stop()
                return True
            else:
                logger.warning(
                    "Connected to MQTT broker but did not receive test message")
                client.loop_stop()
                return False
        else:
            logger.error("Failed to connect to MQTT broker within timeout")
            client.loop_stop()
            return False
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {str(e)}")
        return False


if __name__ == "__main__":
    print("=== IoT Platform Connection Test ===")
    print("This script will test connections to MongoDB, InfluxDB and MQTT broker")
    print("Make sure you have updated settings.py with your connection details")
    print()

    mongodb_success = test_mongodb_connection()
    print()

    influxdb_success = test_influxdb_connection()
    print()

    mqtt_success = test_mqtt_connection()
    print()

    print("=== Connection Test Results ===")
    print(f"MongoDB: {'✅ Connected' if mongodb_success else '❌ Failed'}")
    print(f"InfluxDB: {'✅ Connected' if influxdb_success else '❌ Failed'}")
    print(f"MQTT: {'✅ Connected' if mqtt_success else '❌ Failed'}")

    if mongodb_success and influxdb_success and mqtt_success:
        print("\n🎉 All connections successful! Your IoT Platform is ready to use with real services.")
    else:
        print("\n⚠️ Some connections failed. Please check the logs above for details.")
        print("Refer to real_services_setup.md for troubleshooting tips.")
