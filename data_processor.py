"""
Data Processor for IoT Platform
Processes MQTT messages and stores data in InfluxDB
"""
import json
import logging
from datetime import datetime
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self, influx_handler, mongo_handler):
        """
        Initialize data processor

        Args:
            influx_handler: InfluxDB handler for data storage
            mongo_handler: MongoDB handler for device management
        """
        self.influx_handler = influx_handler
        self.mongo_handler = mongo_handler

    def process_mqtt_message(self, device_id, measurement, payload):
        """
        Process an MQTT message

        Args:
            device_id (str): Device ID extracted from MQTT topic
            measurement (str): Measurement name extracted from MQTT topic
            payload (dict): MQTT payload as a dictionary

        Returns:
            bool: True if successful, False otherwise
        """
        logger.debug(
            f"Processing MQTT message for device {device_id}, measurement {measurement}")

        try:
            # Update device last seen timestamp in MongoDB
            if self.mongo_handler and self.mongo_handler.is_connected():
                device = self.mongo_handler.get_device(device_id)
                if device:
                    # Update device last seen timestamp and status to Online
                    self.mongo_handler.update_device_status(
                        device_id, "Online")
                    self.mongo_handler.update_device_last_seen(device_id)
                    logger.debug(
                        f"Updated device {device_id} status to Online and last_seen timestamp")
                else:
                    logger.warning(f"Device {device_id} not found in database")

            # Store data in InfluxDB
            if self.influx_handler and self.influx_handler.is_connected():
                # Extract value from payload
                value = payload.get('value')
                if value is None:
                    logger.warning(f"No value in payload: {payload}")
                    return False

                # Extract timestamp from payload or use current time
                timestamp = payload.get('timestamp')
                if timestamp:
                    try:
                        timestamp = datetime.fromisoformat(
                            timestamp.replace('Z', '+00:00'))
                    except:
                        # If timestamp format is invalid, use current time
                        timestamp = datetime.utcnow()
                        logger.warning(
                            f"Invalid timestamp format in payload, using current time")
                else:
                    # If no timestamp provided, use current time
                    timestamp = datetime.utcnow()

                # Extract other fields from payload
                fields = {}
                for key, val in payload.items():
                    if key not in ['device_id', 'timestamp']:
                        fields[key] = val

                # Store data point in InfluxDB
                point = {
                    "measurement": measurement,
                    "tags": {
                        "device_id": device_id
                    },
                    "time": timestamp,
                    "fields": fields
                }

                success = self.influx_handler.write_data_point(point)
                if success:
                    logger.debug(
                        f"Data point for device {device_id} stored in InfluxDB")
                    return True
                else:
                    logger.warning(
                        f"Failed to store data point for device {device_id} in InfluxDB")
                    return False
            else:
                logger.warning("InfluxDB handler not available")
                return False

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            return False

    def process_data_batch(self, data_batch):
        """
        Process a batch of data

        Args:
            data_batch (list): List of data points

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Store data batch in InfluxDB
            if self.influx_handler and self.influx_handler.is_connected():
                success = self.influx_handler.write_data_points(data_batch)
                if success:
                    logger.debug(
                        f"Data batch with {len(data_batch)} points stored in InfluxDB")
                    return True
                else:
                    logger.warning(f"Failed to store data batch in InfluxDB")
                    return False
            else:
                logger.warning("InfluxDB handler not available")
                return False
        except Exception as e:
            logger.error(f"Error processing data batch: {e}")
            return False

    def analyze_time_series(self, device_id, measurement, start_time, end_time):
        """
        Analyze time series data

        Args:
            device_id (str): Device ID
            measurement (str): Measurement name
            start_time (datetime): Start time
            end_time (datetime): End time

        Returns:
            dict: Analysis results
        """
        try:
            # Query data from InfluxDB
            if self.influx_handler and self.influx_handler.is_connected():
                data = self.influx_handler.query_device_data(
                    device_id, start_time, end_time, measurement)

                if not data:
                    logger.warning(f"No data found for device {device_id}")
                    return {"error": "No data found"}

                # Perform basic analysis
                values = [point.get('value', 0)
                          for point in data if 'value' in point]

                if not values:
                    logger.warning(
                        f"No values found in data for device {device_id}")
                    return {"error": "No values found in data"}

                # Calculate statistics
                count = len(values)
                total = sum(values)
                avg = total / count if count > 0 else 0
                minimum = min(values) if values else 0
                maximum = max(values) if values else 0

                return {
                    "device_id": device_id,
                    "measurement": measurement,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "statistics": {
                        "count": count,
                        "total": total,
                        "average": avg,
                        "min": minimum,
                        "max": maximum
                    }
                }
            else:
                logger.warning("InfluxDB handler not available")
                return {"error": "InfluxDB service not available"}
        except Exception as e:
            logger.error(f"Error analyzing time series data: {e}")
            return {"error": str(e)}
