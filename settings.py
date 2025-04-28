"""
Settings module for IoT Platform
Centralizes configuration for both FastAPI and Streamlit apps
"""
import os

# Server settings
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000
STREAMLIT_PORT = 5000

# Default API URL
API_URL = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}"


# Database settings
MONGODB_URI = "mongodb://127.0.0.1:27017"
MONGODB_DATABASE = "IoT-Course-project"  # Changed to match your database name

# InfluxDB settings
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "yTmKfYQV55qJyWlUTi9Ms8YdYz6T1cZPR1qfIJzX_F_bcSNa89oYQLxSmR5t7GoWxrSiaKoCu9toSZZqVMmYfQ=="
INFLUXDB_ORG = "ait"
INFLUXDB_BUCKET = "iot_data"

# MQTT settings
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_USERNAME = ""
MQTT_PASSWORD = ""

# Auth settings
SECRET_KEY = ""
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Get settings from environment variables if available
API_URL = os.getenv("API_URL", API_URL)
MONGODB_URI = os.getenv("MONGODB_URI", MONGODB_URI)
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", MONGODB_DATABASE)
INFLUXDB_URL = os.getenv("INFLUXDB_URL", INFLUXDB_URL)
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", INFLUXDB_TOKEN)
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", INFLUXDB_ORG)
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", INFLUXDB_BUCKET)
MQTT_BROKER = os.getenv("MQTT_BROKER", MQTT_BROKER)
MQTT_PORT = int(os.getenv("MQTT_PORT", MQTT_PORT))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", MQTT_USERNAME)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", MQTT_PASSWORD)
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)
