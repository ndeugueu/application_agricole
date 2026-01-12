"""
Identity & Access Service
FastAPI application for authentication and authorization
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.database import create_db_engine, get_session_factory, get_db_session, Base
from shared.auth import (
    get_password_hash,
    verify_password,
    create_token_pair,
    decode_token,
    get_current_user,
    require_roles,
    Roles
)
from shared.logging_config import configure_logging
from shared.events import EventPublisher

import models
import schemas

# Initialize logging
logger = configure_logging("identity-service")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_db_engine(DATABASE_URL)
SessionFactory = get_session_factory(engine)

# Create tables (dev only; prefer migrations in prod)
if os.getenv("AUTO_CREATE_DB", "true").lower() == "true":
    Base.metadata.create_all(bind=engine)

# Event publisher
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
event_publisher = EventPublisher(RABBITMQ_URL, "identity-service") if RABBITMQ_URL else None

# FastAPI app
app = FastAPI(
    title="Identity & Access Service",
    description="Authentication and authorization microservice",
    version="1.0.0"
)


# Dependency to get database session
def get_db():
    with get_db_session(SessionFactory) as session:
        yield session


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Identity service starting up")
    if event_publisher:
        event_publisher.connect()

    # Create default roles and admin user if not exists
    with get_db_session(SessionFactory) as db:
        create_default_data(db)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Identity service shutting down")
    if event_publisher:
        event_publisher.close()


def create_default_data(db: Session):
    """Create default roles and admin user"""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@agricole.com")
    admin_full_name = os.getenv("ADMIN_FULL_NAME", "Administrateur Systeme")

    # Create default permissions
    default_permissions = [
        {"name": "farm:read", "resource": "farm", "action": "read", "description": "Read farm data"},
        {"name": "farm:write", "resource": "farm", "action": "write", "description": "Create/update farm data"},
        {"name": "inventory:read", "resource": "inventory", "action": "read", "description": "Read inventory"},
        {"name": "inventory:write", "resource": "inventory", "action": "write", "description": "Manage inventory"},
        {"name": "sales:read", "resource": "sales", "action": "read", "description": "Read sales"},
        {"name": "sales:write", "resource": "sales", "action": "write", "description": "Create sales"},
        {"name": "accounting:read", "resource": "accounting", "action": "read", "description": "Read accounting"},
        {"name": "accounting:write", "resource": "accounting", "action": "write", "description": "Manage accounting"},
        {"name": "users:manage", "resource": "users", "action": "manage", "description": "Manage users"},
    ]

    permissions = {}
    for perm_data in default_permissions:
        perm = db.query(models.Permission).filter_by(name=perm_data["name"]).first()
        if not perm:
            perm = models.Permission(**perm_data)
            db.add(perm)
            db.flush()
        permissions[perm_data["name"]] = perm

    # Create default roles
    roles_config = {
        Roles.ADMIN: {
            "description": "Administrateur système - accès complet",
            "permissions": list(permissions.values())
        },
        Roles.GESTIONNAIRE: {
            "description": "Gestionnaire - gestion opérationnelle",
            "permissions": [p for name, p in permissions.items() if "manage" not in name or "users" not in name]
        },
        Roles.AGENT_TERRAIN: {
            "description": "Agent terrain - saisie données terrain",
            "permissions": [p for name, p in permissions.items() if "farm" in name or "inventory:read" in name]
        },
        Roles.COMPTABLE: {
            "description": "Comptable - gestion comptabilité et TVA",
            "permissions": [p for name, p in permissions.items() if "accounting" in name or "sales:read" in name]
        }
    }

    roles = {}
    for role_name, role_config in roles_config.items():
        role = db.query(models.Role).filter_by(name=role_name).first()
        if not role:
            role = models.Role(
                name=role_name,
                description=role_config["description"],
                is_system_role=True
            )
            db.add(role)
            db.flush()
        role.permissions = role_config["permissions"]
        roles[role_name] = role

    # Create default admin user
    admin = db.query(models.User).filter_by(username=admin_username).first()
    if not admin:
        if not admin_password:
            logger.warning("ADMIN_PASSWORD not set; skipping default admin user creation.")
        else:
            admin = models.User(
                username=admin_username,
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                full_name=admin_full_name,
                is_active=True,
                is_superuser=True
            )
            admin.roles = [roles[Roles.ADMIN]]
            db.add(admin)
            logger.info("Default admin user created", username=admin_username)
    else:
        if admin.email.endswith(".local"):
            admin.email = admin_email


    db.commit()


# ============================================
# Authentication Endpoints
# ============================================

@app.post("/api/v1/auth/login", response_model=schemas.LoginResponse)
async def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens"""
    user = db.query(models.User).filter(models.User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Create tokens
    role_names = [role.name for role in user.roles]
    scopes = [perm.name for role in user.roles for perm in role.permissions]

    tokens = create_token_pair(
        user_id=str(user.id),
        username=user.username,
        roles=role_names,
        scopes=scopes
    )

    # Store refresh token
    refresh_token_record = models.RefreshToken(
        token=tokens.refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        device_info=login_data.device_info
    )
    db.add(refresh_token_record)

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Publish event
    if event_publisher:
        try:
            event_publisher.publish_event(
                "user.logged_in",
                {"user_id": str(user.id), "username": user.username}
            )
        except Exception as exc:
            logger.warning("Event publish failed", error=str(exc), event="user.logged_in")

    logger.info("User logged in", user_id=str(user.id), username=user.username)

    return schemas.LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=schemas.UserResponse.model_validate(user)
    )


@app.post("/api/v1/auth/refresh", response_model=schemas.TokenResponse)
async def refresh_token(request: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    token_record = db.query(models.RefreshToken).filter_by(
        token=request.refresh_token,
        is_revoked=False
    ).first()

    if not token_record or token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user = token_record.user
    role_names = [role.name for role in user.roles]
    scopes = [perm.name for role in user.roles for perm in role.permissions]

    tokens = create_token_pair(
        user_id=str(user.id),
        username=user.username,
        roles=role_names,
        scopes=scopes
    )

    # Revoke old refresh token and create new one
    token_record.is_revoked = True
    new_refresh_token = models.RefreshToken(
        token=tokens.refresh_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        device_info=token_record.device_info
    )
    db.add(new_refresh_token)
    db.commit()

    return schemas.TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token
    )


@app.post("/api/v1/auth/logout")
async def logout(
    request: schemas.RefreshTokenRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke refresh token"""
    token_record = db.query(models.RefreshToken).filter_by(token=request.refresh_token).first()
    if token_record:
        token_record.is_revoked = True
        db.commit()

    logger.info("User logged out", user_id=current_user.user_id)
    return {"message": "Logged out successfully"}


# ============================================
# User Management Endpoints
# ============================================

@app.post("/api/v1/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: schemas.UserCreate,
    current_user = Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Create a new user"""
    # Check if username or email already exists
    if db.query(models.User).filter(models.User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")

    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        is_active=True,
        is_superuser=False
    )

    # Assign roles
    if user_data.role_ids:
        roles = db.query(models.Role).filter(models.Role.id.in_(user_data.role_ids)).all()
        user.roles = roles

    db.add(user)
    db.commit()
    db.refresh(user)

    # Publish event
    if event_publisher:
        try:
            event_publisher.publish_event(
                "user.created",
                {"user_id": str(user.id), "username": user.username, "email": user.email}
            )
        except Exception as exc:
            logger.warning("Event publish failed", error=str(exc), event="user.created")

    logger.info("User created", user_id=str(user.id), username=user.username)
    return schemas.UserResponse.model_validate(user)


@app.get("/api/v1/users/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    user = db.query(models.User).filter(models.User.id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserResponse.model_validate(user)


@app.get("/api/v1/users", response_model=List[schemas.UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """List all users"""
    users = db.query(models.User).offset(skip).limit(limit).all()
    return [schemas.UserResponse.model_validate(user) for user in users]


@app.get("/api/v1/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: str,
    current_user = Depends(require_roles([Roles.ADMIN, Roles.GESTIONNAIRE])),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserResponse.model_validate(user)


# ============================================
# Role Management Endpoints
# ============================================

@app.get("/api/v1/roles", response_model=List[schemas.RoleResponse])
async def list_roles(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all roles"""
    roles = db.query(models.Role).all()
    return [schemas.RoleResponse.model_validate(role) for role in roles]


@app.get("/api/v1/permissions", response_model=List[schemas.PermissionResponse])
async def list_permissions(
    current_user = Depends(require_roles([Roles.ADMIN])),
    db: Session = Depends(get_db)
):
    """List all permissions"""
    permissions = db.query(models.Permission).all()
    return [schemas.PermissionResponse.model_validate(perm) for perm in permissions]


# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "identity-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
