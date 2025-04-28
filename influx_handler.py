from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import logging
from datetime import datetime, timedelta
import math
import random
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InfluxDBHandler:
    def __init__(self, url, token, org, bucket):
        """
        Initialize InfluxDB client

        Args:
            url (str): InfluxDB server URL
            token (str): InfluxDB API token
            org (str): InfluxDB organization
            bucket (str): InfluxDB bucket
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket

        # Initialize client
        try:
            self.client = InfluxDBClient(url=url, token=token, org=org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info(f"Connected to InfluxDB at {url}")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            self.client = None
            self.write_api = None
            self.query_api = None

    def is_connected(self):
        """
        Check if connected to InfluxDB

        Returns:
            bool: True if connected, False otherwise
        """
        return self.client is not None and self.write_api is not None

    def write_data(self, device_id, measurement, data):
        """
        Write data to InfluxDB

        Args:
            device_id (str): Device ID
            measurement (str): Measurement name
            data (dict): Data to write

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Not connected to InfluxDB")
            return False

        try:
            # Create point
            point = Point(measurement)
            point.tag("device_id", device_id)

            # Add fields based on data type
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    point.field(key, value)
                else:
                    point.field(key, str(value))

            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=point)
            logger.info(f"Wrote data for device {device_id} to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Failed to write data to InfluxDB: {e}")
            return False

    def get_device_data(self, device_id, start_time=None, end_time=None, measurement=None):
        """
        Get data for a device

        Args:
            device_id (str): Device ID
            start_time (datetime): Start time for query (default: 24 hours ago)
            end_time (datetime): End time for query (default: now)
            measurement (str): Measurement name (default: all measurements)

        Returns:
            pd.DataFrame: Data for the device
        """

        if device_id.startswith('demo-'):
            # Set default time range if not provided
            if start_time is None:
                start_time = datetime.now() - timedelta(days=1)
            if end_time is None:
                end_time = datetime.now()

            # Generate time points (every 10 minutes)
            time_points = []
            current = start_time
            while current <= end_time:
                time_points.append(current)
                current += timedelta(minutes=10)

            # Create dataframe columns
            data = {
                'timestamp': time_points,
                'device_id': [device_id] * len(time_points),
                'measurement': [],
                'field': [],
                'value': []
            }

            if 'temp' in device_id:

                base_temp = 21.0
                temp_values = []
                for i in range(len(time_points)):

                    hour_factor = time_points[i].hour / 24.0
                    temp = base_temp + 3 * \
                        math.sin(hour_factor * 2 * math.pi) + \
                        random.uniform(-0.5, 0.5)
                    temp_values.append(round(temp, 1))

                humidity_values = []
                for i in range(len(time_points)):

                    temp_offset = temp_values[i] - base_temp
                    humidity = 50 - (temp_offset * 2) + random.uniform(-5, 5)
                    humidity_values.append(
                        round(max(30, min(70, humidity)), 1))

                battery_values = []
                for i in range(len(time_points)):
                    # Slow linear decline
                    battery = 100 - (i * 15 / len(time_points)
                                     ) + random.uniform(-1, 1)
                    battery_values.append(round(battery, 1))

                # Add to dataframe
                data['measurement'] = ['sensors'] * len(time_points) * 3
                data['field'] = (['temperature'] * len(time_points) +
                                 ['humidity'] * len(time_points) +
                                 ['battery'] * len(time_points))
                data['value'] = temp_values + humidity_values + battery_values

                # Expand other columns to match
                data['timestamp'] = time_points * 3
                data['device_id'] = [device_id] * len(time_points) * 3

            elif 'humid' in device_id:
                # Humidity data (50-70% range)
                base_humidity = 60.0
                humidity_values = []
                for i in range(len(time_points)):
                    # Create a realistic humidity pattern
                    time_factor = time_points[i].hour / 24.0
                    humidity = base_humidity - 10 * \
                        math.sin(time_factor * 2 * math.pi) + \
                        random.uniform(-3, 3)
                    humidity_values.append(
                        round(max(30, min(90, humidity)), 1))

                # Temperature data (relatively stable)
                base_temp = 22.0
                temp_values = []
                for i in range(len(time_points)):
                    temp = base_temp + random.uniform(-1.5, 1.5)
                    temp_values.append(round(temp, 1))

                # Battery data (95% down to 80%)
                battery_values = []
                for i in range(len(time_points)):
                    battery = 95 - (i * 15 / len(time_points)
                                    ) + random.uniform(-1, 1)
                    battery_values.append(round(battery, 1))

                # Add to dataframe
                data['measurement'] = ['sensors'] * len(time_points) * 3
                data['field'] = (['humidity'] * len(time_points) +
                                 ['temperature'] * len(time_points) +
                                 ['battery'] * len(time_points))
                data['value'] = humidity_values + temp_values + battery_values

                # Expand other columns to match
                data['timestamp'] = time_points * 3
                data['device_id'] = [device_id] * len(time_points) * 3

            return pd.DataFrame(data)

        if not self.is_connected():
            logger.warning("Not connected to InfluxDB")
            return pd.DataFrame()

        try:
            # Set default time range if not provided
            if start_time is None:
                start_time = datetime.now() - timedelta(days=1)
            if end_time is None:
                end_time = datetime.now()

            # Convert datetime to RFC3339 format
            start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

            # Build query
            measurement_filter = f'r["_measurement"] == "{measurement}"' if measurement else ""

            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: {start_time_str}, stop: {end_time_str})
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
            '''

            if measurement_filter:
                query += f'|> filter(fn: (r) => {measurement_filter})'

            # Add this line for descending order
            query += ' |> sort(columns: ["_time"], desc: true)'

            # Execute query
            result = self.query_api.query_data_frame(query)

            # Process result
            if result is not None and not result.empty:
                # Convert to pandas DataFrame
                df = pd.DataFrame(result)

                # Rename columns for clarity
                if '_measurement' in df.columns:
                    df = df.rename(columns={'_measurement': 'measurement'})
                if '_field' in df.columns:
                    df = df.rename(columns={'_field': 'field'})
                if '_value' in df.columns:
                    df = df.rename(columns={'_value': 'value'})
                if '_time' in df.columns:
                    df = df.rename(columns={'_time': 'timestamp'})

                return df
            else:
                logger.info(f"No data found for device {device_id}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Failed to query data from InfluxDB: {e}")
            return pd.DataFrame()

    def get_latest_data(self, device_id):
        """
        Get latest data for a device

        Args:
            device_id (str): Device ID

        Returns:
            dict: Latest data for the device
        """
        # For demo devices, return simulated sensor data
        if device_id.startswith('demo-'):
            import random
            import time

            # Return different data depending on device type
            if 'temp' in device_id:
                return {
                    'temperature': round(random.uniform(18.0, 25.0), 1),
                    'battery': random.randint(60, 100),
                    'humidity': round(random.uniform(30.0, 60.0), 1),
                    'last_report': time.time()
                }
            elif 'humid' in device_id:
                return {
                    'humidity': round(random.uniform(35.0, 75.0), 1),
                    'battery': random.randint(50, 95),
                    'temperature': round(random.uniform(19.0, 24.0), 1),
                    'last_report': time.time()
                }
            else:
                return {
                    'value': random.randint(0, 100),
                    'battery': random.randint(30, 100),
                    'last_report': time.time()
                }

        if not self.is_connected():
            logger.warning("Not connected to InfluxDB")
            return {}

        try:
            # Query for latest data
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> last()
            '''

            # Execute query
            result = self.query_api.query_data_frame(query)

            # Process result
            if result is not None and not result.empty:
                # Convert to dict of latest values by field
                latest_data = {}
                for _, row in result.iterrows():
                    field = row.get('_field', '')
                    value = row.get('_value', '')
                    latest_data[field] = value

                return latest_data
            else:
                logger.info(f"No data found for device {device_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to query latest data from InfluxDB: {e}")
            return {}

    def get_measurements(self):
        """
        Get all measurements

        Returns:
            list: List of measurement names
        """
        if not self.is_connected():
            logger.warning("Not connected to InfluxDB")
            return []

        try:
            # Query for measurements
            query = f'''
                import "influxdata/influxdb/schema"
                schema.measurements(bucket: "{self.bucket}")
            '''

            # Execute query
            result = self.query_api.query(query)

            # Process result
            measurements = []
            for table in result:
                for record in table.records:
                    measurements.append(record.values.get('_value'))

            return measurements
        except Exception as e:
            logger.error(f"Failed to query measurements from InfluxDB: {e}")
            return []

    def _get_device_status(self, device_id):
        """
        Get a device's status based on recent data

        Args:
            device_id (str): Device ID

        Returns:
            str: 'Online' or 'Offline'
        """
        if not self.is_connected():
            logger.warning("Not connected to InfluxDB")
            return 'Offline'

        try:
            # Query for latest data in the last 5 minutes
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -5m)
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> count()
            '''

            # Execute query
            result = self.query_api.query(query)

            # Check if any data points were found
            for table in result:
                for record in table.records:
                    if record.get_value() > 0:
                        return 'Online'

            return 'Offline'
        except Exception as e:
            logger.error(f"Failed to determine device status: {e}")
            return 'Offline'
