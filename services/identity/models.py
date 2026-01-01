"""
Identity Service Database Models
Users, Roles, Permissions, Sessions
"""
from sqlalchemy import Column, String, Boolean, Table, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.database import Base, TimestampMixin


# Many-to-many relationship table for users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
)

# Many-to-many relationship table for roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    phone_number = Column(String(20))
    last_login_at = Column(DateTime(timezone=True))

    # Relationships
    roles = relationship('Role', secondary=user_roles, back_populates='users', lazy='selectin')
    refresh_tokens = relationship('RefreshToken', back_populates='user', cascade='all, delete-orphan')


class Role(Base, TimestampMixin):
    """Role model for RBAC"""
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    is_system_role = Column(Boolean, default=False, nullable=False)  # Cannot be deleted

    # Relationships
    users = relationship('User', secondary=user_roles, back_populates='roles')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles', lazy='selectin')


class Permission(Base, TimestampMixin):
    """Permission model for fine-grained access control"""
    __tablename__ = 'permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(50), nullable=False)  # e.g., "farm", "inventory", "sales"
    action = Column(String(50), nullable=False)    # e.g., "read", "write", "delete"
    description = Column(String(255))

    # Relationships
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')


class RefreshToken(Base, TimestampMixin):
    """Refresh token for JWT authentication"""
    __tablename__ = 'refresh_tokens'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(500), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    device_info = Column(String(255))  # Optional: store device/browser info

    # Relationships
    user = relationship('User', back_populates='refresh_tokens')
