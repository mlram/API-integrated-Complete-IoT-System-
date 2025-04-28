"""
Demo data generator for IoT Platform
Provides fallback data when external services are unavailable
"""

import random
import time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DemoDataGenerator:
    """Generates demo data for IoT Platform when real data sources are unavailable"""
    
    def __init__(self):
        """Initialize with default demo data"""
        self.users = [
            {"username": "admin", "password": "admin123", "role": "Admin", "created_at": self._iso_time(days_ago=30)},
            {"username": "user1", "password": "user123", "role": "User", "created_at": self._iso_time(days_ago=25)},
            {"username": "guest", "password": "guest123", "role": "Guest", "created_at": self._iso_time(days_ago=20)}
        ]
        
        self.projects = [
            {"project_id": "smart-home", "name": "Smart Home", "description": "Smart home automation project", 
             "owner": "admin", "created_at": self._iso_time(days_ago=28)},
            {"project_id": "factory-sensors", "name": "Factory Sensors", "description": "Factory floor monitoring", 
             "owner": "admin", "created_at": self._iso_time(days_ago=26)},
            {"project_id": "weather-station", "name": "Weather Station", "description": "Outdoor weather monitoring", 
             "owner": "user1", "created_at": self._iso_time(days_ago=15)}
        ]
        
        self.devices = [
            {"device_id": "temp-sensor-1", "name": "Temperature Sensor 1", "device_type": "Temperature Sensor", 
             "location": "Living Room", "project_id": "smart-home", "last_seen": self._iso_time(mins_ago=5)},
            {"device_id": "humidity-1", "name": "Humidity Sensor 1", "device_type": "Humidity Sensor", 
             "location": "Kitchen", "project_id": "smart-home", "last_seen": self._iso_time(mins_ago=7)},
            {"device_id": "motion-1", "name": "Motion Sensor 1", "device_type": "Motion Sensor", 
             "location": "Front Door", "project_id": "smart-home", "last_seen": self._iso_time(mins_ago=12)},
            {"device_id": "temp-factory-1", "name": "Factory Temperature", "device_type": "Temperature Sensor", 
             "location": "Assembly Line", "project_id": "factory-sensors", "last_seen": self._iso_time(mins_ago=3)},
            {"device_id": "vibration-1", "name": "Vibration Sensor", "device_type": "Vibration Sensor", 
             "location": "Motor Housing", "project_id": "factory-sensors", "last_seen": self._iso_time(mins_ago=8)},
            {"device_id": "outdoor-temp", "name": "Outdoor Temperature", "device_type": "Temperature Sensor", 
             "location": "Backyard", "project_id": "weather-station", "last_seen": self._iso_time(mins_ago=6)},
            {"device_id": "wind-speed", "name": "Wind Sensor", "device_type": "Wind Sensor", 
             "location": "Roof", "project_id": "weather-station", "last_seen": self._iso_time(mins_ago=6)},
            {"device_id": "rainfall", "name": "Rain Gauge", "device_type": "Precipitation Sensor", 
             "location": "Garden", "project_id": "weather-station", "last_seen": self._iso_time(mins_ago=6)}
        ]
    
    def _iso_time(self, days_ago=0, mins_ago=0):
        """Generate ISO format time for a past date"""
        past_time = datetime.now() - timedelta(days=days_ago, minutes=mins_ago)
        return past_time.isoformat()
    
    def get_users(self, username=None):
        """Get demo users"""
        if username:
            return next((user for user in self.users if user["username"] == username), None)
        return self.users
    
    def get_projects(self, project_id=None, owner=None):
        """Get demo projects with optional filtering"""
        if project_id:
            return next((project for project in self.projects if project["project_id"] == project_id), None)
        if owner:
            return [project for project in self.projects if project["owner"] == owner]
        return self.projects
    
    def get_devices(self, device_id=None, project_id=None):
        """Get demo devices with optional filtering"""
        if device_id:
            return next((device for device in self.devices if device["device_id"] == device_id), None)
        if project_id:
            return [device for device in self.devices if device["project_id"] == project_id]
        return self.devices
    
    def generate_device_data(self, device_id, start_time=None, end_time=None, num_points=100):
        """Generate synthetic device data for a specific time range
        
        Args:
            device_id (str): Device ID
            start_time (datetime): Start time for data (defaults to 24h ago)
            end_time (datetime): End time for data (defaults to now)
            num_points (int): Number of data points to generate
            
        Returns:
            list: List of data points
        """
        # Set default time range if not provided
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)
        if end_time is None:
            end_time = datetime.now()
        
        # Get device info to determine data type
        device = self.get_devices(device_id)
        if not device:
            return []
        
        data_points = []
        time_delta = (end_time - start_time) / max(1, num_points - 1)
        
        for i in range(num_points):
            timestamp = start_time + (time_delta * i)
            
            # Generate appropriate data based on device type
            if "Temperature" in device["device_type"]:
                if "outdoor" in device_id or "weather" in device["project_id"]:
                    # Outdoor temperatures fluctuate more
                    base_temp = 15  # Base temperature in Celsius
                    daily_variation = 10  # Daily temperature variation
                    random_factor = 3  # Random noise
                    
                    # Calculate time of day factor (0-1)
                    hour = timestamp.hour
                    time_factor = 1 - abs((hour - 14) / 12)  # Peak at 2 PM
                    
                    value = base_temp + (daily_variation * time_factor) + random.uniform(-random_factor, random_factor)
                else:
                    # Indoor temperatures are more stable
                    value = 22 + random.uniform(-2, 2)  # Indoor temperature around 22°C
                
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 1),
                    "field": "temperature",
                    "unit": "°C"
                })
            
            elif "Humidity" in device["device_type"]:
                value = 50 + random.uniform(-20, 20)  # Humidity percentage
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 1),
                    "field": "humidity",
                    "unit": "%"
                })
            
            elif "Motion" in device["device_type"]:
                # Motion sensor has boolean values
                # More likely to be motion during day hours
                hour = timestamp.hour
                if 8 <= hour <= 22:
                    prob = 0.3  # 30% chance of motion during day
                else:
                    prob = 0.05  # 5% chance of motion during night
                
                value = random.random() < prob
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": value,
                    "field": "motion",
                    "unit": "boolean"
                })
            
            elif "Vibration" in device["device_type"]:
                # Vibration sensor - higher during working hours
                hour = timestamp.hour
                if 9 <= hour <= 17 and timestamp.weekday() < 5:  # Working hours on weekdays
                    value = 0.5 + random.uniform(0, 0.5)  # Higher vibration
                else:
                    value = random.uniform(0, 0.2)  # Lower vibration when not working
                
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 3),
                    "field": "vibration",
                    "unit": "g"
                })
            
            elif "Wind" in device["device_type"]:
                value = random.uniform(0, 30)  # Wind speed in km/h
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 1),
                    "field": "wind_speed",
                    "unit": "km/h"
                })
            
            elif "Precipitation" in device["device_type"] or "Rain" in device["device_type"]:
                # Rainfall - mostly zero with occasional showers
                rain_chance = 0.2  # 20% chance of rain
                if random.random() < rain_chance:
                    value = random.uniform(0.1, 5)  # Rainfall in mm
                else:
                    value = 0
                
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 1),
                    "field": "rainfall",
                    "unit": "mm"
                })
            
            else:
                # Generic sensor - generate numeric value between 0-100
                value = random.uniform(0, 100)
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 1),
                    "field": "value",
                    "unit": ""
                })
        
        return data_points
    
    def get_device_latest_data(self, device_id):
        """Get latest data point for a device
        
        Args:
            device_id (str): Device ID
            
        Returns:
            dict: Latest data values
        """
        device = self.get_devices(device_id)
        if not device:
            return {}
        
        # Generate a single recent data point
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        data = self.generate_device_data(device_id, one_minute_ago, now, 1)
        
        if not data:
            return {}
        
        # Format as a dictionary of fields
        result = {}
        for point in data:
            result[point['field']] = {
                'value': point['value'],
                'unit': point.get('unit', ''),
                'timestamp': point['timestamp']
            }
        
        return result


# Create a singleton instance
demo_data = DemoDataGenerator()