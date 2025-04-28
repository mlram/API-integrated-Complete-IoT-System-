IoT Platform Local Setup Guide

Essential Files

These are the core files you need to run the application locally:

Backend (FastAPI)

simplified_api.py - Main API server
api_models.py - Pydantic models for API
settings.py - Configuration settings
local_auth.py - Authentication logic
demo_data.py - Fallback data generation
users.json - User credentials
Frontend (Streamlit)

api_demo.py - Main Streamlit interface
api_client.py - API client for frontend
device_connectivity.py - Device visualization components
Utility Files

utils.py - Utility functions
requirements_local.txt - Dependencies list
Default Credentials

Admin: username admin, password admin123
User: username user, password user123
Guest: username guest, password guest123
Database Notes

The application uses fallback mechanisms if databases are unavailable:

MongoDB: Used for device and user storage
InfluxDB: Used for time-series data
