import streamlit as st
import os

def initialize_session_state():
    """Initialize session state variables with default values"""
    # Auth state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    if 'username' not in st.session_state:
        st.session_state.username = None
        
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    # InfluxDB settings
    if 'influxdb_url' not in st.session_state:
        st.session_state.influxdb_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    
    if 'influxdb_token' not in st.session_state:
        st.session_state.influxdb_token = os.getenv('INFLUXDB_TOKEN', '')
    
    if 'influxdb_org' not in st.session_state:
        st.session_state.influxdb_org = os.getenv('INFLUXDB_ORG', 'iot_platform')
    
    if 'influxdb_bucket' not in st.session_state:
        st.session_state.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'iot_data')
    
    # MongoDB settings - Use localhost for greater reliability
    if 'mongodb_connection_string' not in st.session_state:
        st.session_state.mongodb_connection_string = os.getenv('MONGODB_CONNECTION_STRING', 'mongodb://localhost:27017/')
    
    if 'mongodb_database' not in st.session_state:
        st.session_state.mongodb_database = os.getenv('MONGODB_DATABASE', 'iot_platform')
    
    # MQTT settings - Use localhost for greater reliability
    if 'mqtt_broker' not in st.session_state:
        st.session_state.mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
    
    if 'mqtt_port' not in st.session_state:
        st.session_state.mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
    
    if 'mqtt_username' not in st.session_state:
        st.session_state.mqtt_username = os.getenv('MQTT_USERNAME', '')
    
    if 'mqtt_password' not in st.session_state:
        st.session_state.mqtt_password = os.getenv('MQTT_PASSWORD', '')
    
    # MQTT monitoring
    if 'mqtt_monitoring' not in st.session_state:
        st.session_state.mqtt_monitoring = False

def format_timestamp(timestamp):
    """Format a timestamp for display"""
    if timestamp is None:
        return "Never"
    
    try:
        # If timestamp is a number (Unix timestamp)
        from datetime import datetime
        return datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        # If already a string or other format
        return str(timestamp)

def generate_device_id():
    """Generate a unique device ID"""
    import uuid
    return f"device-{uuid.uuid4().hex[:8]}"

def parse_mqtt_topic(topic):
    """Parse an MQTT topic into components"""
    parts = topic.split('/')
    result = {
        'full_topic': topic,
        'levels': len(parts)
    }
    
    # Handle common IoT topic patterns
    if len(parts) >= 2 and parts[0] == 'devices':
        result['type'] = 'device'
        result['device_id'] = parts[1]
        
        if len(parts) >= 3:
            result['channel'] = parts[2]
    
    return result

def get_color_for_value(value, min_val, max_val):
    """Get a color based on a value's position in a range"""
    try:
        value = float(value)
        min_val = float(min_val)
        max_val = float(max_val)
        
        # Normalize to 0-1
        normalized = (value - min_val) / (max_val - min_val)
        
        if normalized < 0.33:
            return "#e74c3c"  # Red
        elif normalized < 0.66:
            return "#f39c12"  # Yellow
        else:
            return "#2ecc71"  # Green
    except (ValueError, TypeError, ZeroDivisionError):
        return "#3498db"  # Default blue
        
def check_user_access(required_role):
    """
    Check if the current user has access based on their role
    
    Args:
        required_role (str): Required role ('Admin' or 'User')
        
    Returns:
        bool: True if user has access, False otherwise
    """
    # If not authenticated, no access
    if not st.session_state.authenticated:
        return False
    
    # Admins have access to everything
    if st.session_state.user_role == 'Admin':
        return True
    
    # User role check
    if required_role == 'User' and st.session_state.user_role == 'User':
        return True
    
    # Default deny
    return False

def create_default_admin(mongo_handler):
    """
    Create a default admin user if no users exist in the system
    
    Args:
        mongo_handler: MongoDB handler instance
    """
    if mongo_handler.is_connected():
        users = mongo_handler.get_users()
        if not users:
            # Create a default admin user
            mongo_handler.add_user('admin', 'admin123', 'Admin')
            st.success("Created default admin user. Username: admin, Password: admin123")
            st.warning("Please change the default password after first login!")
            return True
    return False
