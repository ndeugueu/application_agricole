"""
Identity Service Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100)
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class PermissionCreate(PermissionBase):
    pass


class PermissionResponse(PermissionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class RoleBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class RoleCreate(RoleBase):
    permission_ids: List[UUID] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=255)
    permission_ids: Optional[List[UUID]] = None


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_system_role: bool
    permissions: List[PermissionResponse]
    created_at: datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role_ids: List[UUID] = []


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_superuser: bool
    roles: List[RoleResponse]
    last_login_at: Optional[datetime]
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str
    device_info: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
