from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Authentication models


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserBase(BaseModel):
    username: str
    role: str = "User"


class UserCreate(UserBase):
    password: str


class User(UserBase):
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# Project models


class ProjectBase(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    owner: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

# Device models


class DeviceBase(BaseModel):
    device_id: str
    name: str
    device_type: Optional[str] = None
    location: Optional[str] = None
    project_id: Optional[str] = None  # Link to project


class DeviceCreate(DeviceBase):
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None


class Device(DeviceBase):
    last_seen: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

# Data models


class DataPoint(BaseModel):
    timestamp: datetime
    value: Union[float, int, str, bool]
    field: str


class DeviceData(BaseModel):
    device_id: str
    data: List[DataPoint]

# Command models


class Command(BaseModel):
    command: str
    payload: Optional[Dict[str, Any]] = None

# MQTT models


class MQTTMessage(BaseModel):
    topic: str
    payload: str
    qos: int = 0
    retain: bool = False

# Response models


class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
