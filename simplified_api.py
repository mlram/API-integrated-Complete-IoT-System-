"""
Simplified FastAPI for the IoT Platform
Fixed version that uses MongoDB properly instead of demo arrays
"""
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import threading
import time
import json
import os
import logging
import jwt
from passlib.context import CryptContext

# Import MongoDB handler
from mongo_handler import MongoDBHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB settings - make sure this matches your actual database
MONGODB_URI = "mongodb://127.0.0.1:27017"
MONGODB_DATABASE = "IoT-Course-project"  # Using your actual database name

# Authentication settings
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password handling
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize handlers
mongo_handler = MongoDBHandler(MONGODB_URI, MONGODB_DATABASE)

# Pydantic models for authentication


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
        # Create default admin user if it doesn't exist
        if not mongo_handler.verify_user("admin", "admin123"):
            mongo_handler.add_user("admin", "admin123", "Admin")
            logger.info("Created default admin user")

        # Create default regular user if it doesn't exist
        if not mongo_handler.verify_user("user", "user123"):
            mongo_handler.add_user("user", "user123", "User")
            logger.info("Created default regular user")

        # Create default guest user if it doesn't exist
        if not mongo_handler.verify_user("guest", "guest123"):
            mongo_handler.add_user("guest", "guest123", "Guest")
            logger.info("Created default guest user")

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
    return {"message": "IoT Platform API is running"}

# Health check endpoint


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mongodb_connected = mongo_handler.is_connected() if mongo_handler else False

    return {
        "success": True,
        "message": "API is running",
        "data": {
            "api": True,
            "ready": ready,
            "services": {
                "mongodb": mongodb_connected
            }
        }
    }

# Authentication functions


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Authentication endpoint


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login"""
    # Authenticate against MongoDB
    user = mongo_handler.verify_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user information
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# JWT token verification


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, role=role)
    except Exception:
        raise credentials_exception

    # Get user from MongoDB
    users = mongo_handler.get_users()
    user = next(
        (user for user in users if user["username"] == token_data.username), None)

    if user is None:
        raise credentials_exception

    return User(username=user["username"], role=user["role"], created_at=user.get("created_at"))

# User endpoint - get current user info


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# Admin-only: Get all users


@app.get("/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Get all users - Admin only"""
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Get all users from MongoDB
    return mongo_handler.get_users()


@app.post("/users")
async def create_user(
    username: str,
    password: str,
    role: str = "User",
    current_user: User = Depends(get_current_user)
):
    """Create a new user - Admin only"""
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Create user in MongoDB
    success = mongo_handler.add_user(username, password, role)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user, username may already exist"
        )

    return {"success": True, "message": f"User {username} created with role {role}"}

# Admin-only: Delete user


@app.delete("/users/{username}")
async def delete_user(username: str, current_user: User = Depends(get_current_user)):
    """Delete a user - Admin only"""
    # Check if user is admin
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Delete user from MongoDB
    success = mongo_handler.remove_user(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} not found"
        )

    return {"success": True, "message": f"User {username} deleted"}


@app.get("/devices")
async def get_devices(current_user: User = Depends(get_current_user)):
    """Get all devices"""

    devices = mongo_handler.get_devices()

    return devices


@app.get("/devices/{device_id}")
async def get_device(device_id: str, current_user: User = Depends(get_current_user)):
    """Get device by ID"""
    # Get device from MongoDB
    device = mongo_handler.get_device(device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    return device

#


@app.post("/devices")
async def create_device(
    device_id: str,
    name: str,
    device_type: Optional[str] = None,
    location: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new device"""
    # Check permissions - allow both Admin and User roles
    if current_user.role == "Guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Validate that a project_id is provided (enforcing hierarchical model)
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID is required when creating a device"
        )

    # Validate project exists
    project = mongo_handler.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )

    # Create device in MongoDB
    success = mongo_handler.add_device(
        device_id, name, device_type, location, project_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create device, device ID may already exist"
        )

    return {
        "success": True,
        "message": f"Device {name} created with ID {device_id}",
        "data": {
            "device_id": device_id,
            "name": name,
            "device_type": device_type,
            "location": location,
            "project_id": project_id,
            "status": "Offline",
            "last_seen": None
        }
    }

# Admin/User: Delete device


@app.delete("/devices/{device_id}")
async def delete_device(device_id: str, current_user: User = Depends(get_current_user)):
    """Delete a device - Admin and User only"""
    # Check permissions
    if current_user.role == "Guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Delete device from MongoDB
    success = mongo_handler.remove_device(device_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )

    return {"success": True, "message": f"Device {device_id} deleted"}

# Get all projects


@app.get("/projects")
async def get_projects(current_user: User = Depends(get_current_user)):
    """Get all projects"""

    projects = mongo_handler.get_projects()

    return projects


@app.get("/projects/{project_id}")
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get project by ID"""

    project = mongo_handler.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )

    return project

# Create project


@app.post("/projects")
async def create_project(
    project_id: str,
    name: str,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""

    if current_user.role == "Guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    success = mongo_handler.create_project(
        project_id, name, current_user.username, description)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create project, project ID may already exist"
        )

    return {
        "success": True,
        "message": f"Project {name} created with ID {project_id}",
        "data": {
            "project_id": project_id,
            "name": name,
            "description": description,
            "owner": current_user.username,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Delete a project - Admin and project owner only"""

    if current_user.role == "Guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    project = mongo_handler.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )

    if current_user.role != "Admin" and project["owner"] != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions - only admin or project owner can delete"
        )

    success = mongo_handler.remove_project(project_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project due to server error"
        )

    return {"success": True, "message": f"Project {project_id} deleted"}


@app.get("/projects/{project_id}/devices")
async def get_project_devices(project_id: str, current_user: User = Depends(get_current_user)):
    """Get devices in a project"""
    # Validate project exists
    project = mongo_handler.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )

    # Get all devices
    devices = mongo_handler.get_devices()

    # Filter by project_id
    project_devices = [device for device in devices if device.get(
        "project_id") == project_id]

    return project_devices
