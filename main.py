"""
Simplified FastAPI for the IoT Platform
This is a minimal version of the API to ensure it starts quickly
"""
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import threading
import time
import json
import os
import math
import random
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication settings

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    username: str
    role: str = "User"
    created_at: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="IoT Platform API",
    description="REST API for IoT platform management and data access",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ready = False

# Background initialization


def initialize_background():
    """Initialize everything in the background"""
    global ready
    try:

        time.sleep(2)
        logger.info("Background initialization complete")
        ready = True
    except Exception as e:
        logger.error(f"Error during background initialization: {e}")


# Start background initialization
threading.Thread(target=initialize_background, daemon=True).start()

# Root endpoint for quick health check


@app.get("/")
async def root():
    """Root endpoint, always returns quickly"""
    return {"message": "IoT Platform API is starting up"}

# Health check endpoint


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "API is running",
        "data": {
            "api": True,
            "ready": ready,
            "services": {
                "influxdb": False,
                "mongodb": False,
                "mqtt": False
            }
        }
    }

# Demo data endpoint


@app.get("/demo/devices")
async def demo_devices():
    """Return some demo devices"""
    return [
        {
            "device_id": "demo-temp-1",
            "name": "Temperature Sensor 1",
            "device_type": "temperature",
            "location": "Living Room",
            "status": "Online"
        },
        {
            "device_id": "demo-temp-2",
            "name": "Temperature Sensor 2",
            "device_type": "temperature",
            "location": "Kitchen",
            "status": "Online"
        },
        {
            "device_id": "demo-humidity-1",
            "name": "Humidity Sensor 1",
            "device_type": "humidity",
            "location": "Bathroom",
            "status": "Online"
        }
    ]

# Demo projects endpoint


@app.get("/demo/projects")
async def demo_projects():
    """Return some demo projects"""
    return [
        {
            "project_id": "home-monitoring",
            "name": "Home Monitoring",
            "description": "Monitoring of home environment",
            "owner": "admin"
        },
        {
            "project_id": "garden-automation",
            "name": "Garden Automation",
            "description": "Automated garden watering system",
            "owner": "admin"
        }
    ]

# Create device class


class Device(BaseModel):
    device_id: str
    name: str
    device_type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    project_id: Optional[str] = None


# Demo device list for management (this is mutable)
DEVICES = [
    {
        "device_id": "demo-temp-1",
        "name": "Temperature Sensor 1",
        "device_type": "temperature",
        "location": "Living Room",
        "status": "Online",
        "project_id": "home-monitoring"
    },
    {
        "device_id": "demo-temp-2",
        "name": "Temperature Sensor 2",
        "device_type": "temperature",
        "location": "Kitchen",
        "status": "Online",
        "project_id": "home-monitoring"
    },
    {
        "device_id": "demo-humidity-1",
        "name": "Humidity Sensor 1",
        "device_type": "humidity",
        "location": "Bathroom",
        "status": "Online",
        "project_id": "home-monitoring"
    },
    {
        "device_id": "demo-soil-1",
        "name": "Soil Moisture Sensor 1",
        "device_type": "soil-moisture",
        "location": "Garden",
        "status": "Online",
        "project_id": "garden-automation"
    }
]

# Demo project list for management
PROJECTS = [
    {
        "project_id": "home-monitoring",
        "name": "Home Monitoring",
        "description": "Monitoring of home environment",
        "owner": "admin"
    },
    {
        "project_id": "garden-automation",
        "name": "Garden Automation",
        "description": "Automated garden watering system",
        "owner": "admin"
    }
]

# Authentication helper functions


def verify_password(plain_password, hashed_password):
    """Verify password against hashed version"""
    if hashed_password.startswith('$2b$'):

        return pwd_context.verify(plain_password, hashed_password)
    else:

        return plain_password == hashed_password


def get_password_hash(password):
    """Hash a password for storing"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # Plain text for demo
        "role": "Admin",
        "created_at": datetime.utcnow().isoformat()
    },
    "user": {
        "username": "user",
        "password": "user123",
        "role": "User",
        "created_at": datetime.utcnow().isoformat()
    },
    "guest": {
        "username": "guest",
        "password": "guest123",
        "role": "Guest",
        "created_at": datetime.utcnow().isoformat()
    }
}

# Authentication endpoint


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login"""
    user = None
    if form_data.username in USERS:
        stored_user = USERS[form_data.username]
        if verify_password(form_data.password, stored_user["password"]):
            user = stored_user

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "User")},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user from token


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role", "User")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except Exception:
        raise credentials_exception

    # Try to find user
    user = USERS.get(token_data.username)

    if user is None:
        raise credentials_exception

    return User(username=user["username"], role=user.get("role", "User"), created_at=user.get("created_at"))

# User info endpoint


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# Get all users (Admin only)


@app.get("/users")
async def get_users(current_user: User = Depends(get_current_user)):
    """Get all users (Admin only)"""
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Return all users (excluding passwords)
    return [
        {
            "username": username,
            "role": user_data["role"],
            "created_at": user_data.get("created_at", "")
        }
        for username, user_data in USERS.items()
    ]

# Delete a user (Admin only)


@app.delete("/users/{username}")
async def delete_user(username: str, current_user: User = Depends(get_current_user)):
    """Delete a user (Admin only)"""
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    # Check if user exists
    if username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} not found"
        )

    # Delete the user
    deleted_user_data = USERS.pop(username)

    # Return success with deleted user info (excluding password)
    return {
        "success": True,
        "message": "User deleted",
        "data": {
            "username": username,
            "role": deleted_user_data["role"],
            "created_at": deleted_user_data.get("created_at", "")
        }
    }

# Get all devices


@app.get("/devices")
async def get_devices(current_user: User = Depends(get_current_user)):
    """Get all devices"""
    # No filtering based on role for this demo
    return DEVICES

# Get a specific device


@app.get("/devices/{device_id}")
async def get_device(device_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific device"""
    for device in DEVICES:
        if device["device_id"] == device_id:
            return device
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    )

# Create a new device (Admin or User role required)


@app.post("/devices")
async def create_device(device: Device, current_user: User = Depends(get_current_user)):
    """Create a new device"""
    # Check permissions - allow both Admin and User roles
    if current_user.role == "Guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if device already exists
    for existing_device in DEVICES:
        if existing_device["device_id"] == device.device_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device with ID {device.device_id} already exists"
            )

    # Validate that a project_id is provided (enforcing hierarchical model)
    if not device.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A device must be associated with a project. Please provide a project_id."
        )

    # Verify the project exists
    project_exists = False
    for project in PROJECTS:
        if project["project_id"] == device.project_id:
            project_exists = True
            break

    if not project_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with ID {device.project_id} does not exist"
        )

    # Create the device
    new_device = device.dict()
    new_device["status"] = "Offline"  # Default status for new devices
    DEVICES.append(new_device)

    return {"success": True, "message": "Device created", "data": new_device}

# Update a device (Admin or User role required)


@app.put("/devices/{device_id}")
async def update_device(
    device_id: str,
    device_updates: dict,
    current_user: User = Depends(get_current_user)
):
    """Update a device"""
    # Check permissions - allow both Admin and User roles
    if current_user.role == "Guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Find the device
    for index, device in enumerate(DEVICES):
        if device["device_id"] == device_id:
            # Update the device
            for key, value in device_updates.items():
                if key not in ["device_id"]:  # Don't allow device_id to be changed
                    DEVICES[index][key] = value
            return {"success": True, "message": "Device updated", "data": DEVICES[index]}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    )

# Delete a device (Admin only)


@app.delete("/devices/{device_id}")
async def delete_device(device_id: str, current_user: User = Depends(get_current_user)):
    """Delete a device"""
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Find and delete the device
    for index, device in enumerate(DEVICES):
        if device["device_id"] == device_id:
            deleted_device = DEVICES.pop(index)
            return {"success": True, "message": "Device deleted", "data": deleted_device}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Device with ID {device_id} not found"
    )

# Device data model


class DataPoint(BaseModel):
    timestamp: datetime
    field: str
    value: Union[float, int, str, bool]

# Device data endpoint


@app.get("/data/{device_id}")
async def get_device_data(
    device_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get data for a specific device"""
    # Find the device first
    device = None
    for d in DEVICES:
        if d["device_id"] == device_id:
            device = d
            break

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    # Generate demo data for the device
    if start is None:
        start = datetime.now() - timedelta(days=1)
    if end is None:
        end = datetime.now()

    # Generate different data based on device type
    device_type = device.get("device_type", "unknown")
    data_points = []

    # Number of data points to generate
    num_points = 100

    # Time between points
    time_delta = (end - start) / num_points

    if device_type == "temperature":

        base_temp = 22.0  # Base temperature
        for i in range(num_points):
            timestamp = start + time_delta * i
            # Add some randomness and a sine wave pattern
            value = base_temp + 2.0 * \
                math.sin(i / 10.0) + random.uniform(-0.5, 0.5)
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "field": "temperature",
                "value": round(value, 1)
            })

    elif device_type == "humidity":

        base_humidity = 45.0
        for i in range(num_points):
            timestamp = start + time_delta * i

            value = base_humidity + 10.0 * \
                math.sin(i / 15.0) + random.uniform(-2, 2)

            value = max(0, min(100, value))
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "field": "humidity",
                "value": round(value, 1)
            })

    elif device_type == "soil-moisture":

        base_moisture = 60.0
        for i in range(num_points):
            timestamp = start + time_delta * i

            day_progress = i / num_points

            if day_progress > 0.2 and day_progress < 0.25 or day_progress > 0.7 and day_progress < 0.75:
                value = base_moisture + random.uniform(-2, 2)
            else:
                value = base_moisture - 20 * \
                    day_progress + random.uniform(-1, 1)

            value = max(0, min(100, value))
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "field": "moisture",
                "value": round(value, 1)
            })

    else:
        # Generic numeric data for unknown device types
        for i in range(num_points):
            timestamp = start + time_delta * i
            value = 50.0 + 25.0 * math.sin(i / 10.0) + random.uniform(-5, 5)
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "field": "value",
                "value": round(value, 1)
            })

    # Return the data
    return {
        "device_id": device_id,
        "data": data_points
    }

# Get devices by project ID


@app.get("/projects/{project_id}/devices")
async def get_project_devices(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all devices for a specific project"""
    # Filter devices by project ID
    project_devices = [d for d in DEVICES if d.get("project_id") == project_id]
    return project_devices

# Get all projects


@app.get("/projects")
async def get_projects(current_user: User = Depends(get_current_user)):
    """Get all projects"""
    # No filtering based on role for this demo
    return PROJECTS

# Get a specific project


@app.get("/projects/{project_id}")
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific project"""
    for project in PROJECTS:
        if project["project_id"] == project_id:
            return project
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Project with ID {project_id} not found"
    )

# Create a new project (Admin or User role required)


@app.post("/projects")
async def create_project(
    project: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    # Check permissions - allow both Admin and User roles
    if current_user.role == "Guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if project already exists
    for existing_project in PROJECTS:
        if existing_project["project_id"] == project["project_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with ID {project['project_id']} already exists"
            )

    # Create the project
    new_project = project.copy()
    new_project["owner"] = current_user.username
    PROJECTS.append(new_project)

    return {"success": True, "message": "Project created", "data": new_project}

# Delete a project (Admin or owner only)


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Delete a project"""
    # Find the project
    for index, project in enumerate(PROJECTS):
        if project["project_id"] == project_id:
            # Check permissions - admin or owner
            if current_user.role != "Admin" and project["owner"] != current_user.username:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )

            deleted_project = PROJECTS.pop(index)
            return {"success": True, "message": "Project deleted", "data": deleted_project}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Project with ID {project_id} not found"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simplified_api:app", host="0.0.0.0", port=8000)
