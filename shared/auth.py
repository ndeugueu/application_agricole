"""
Shared authentication and authorization utilities
JWT token management and RBAC
"""
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    username: str
    roles: List[str]
    scopes: List[str] = []


class TokenPair(BaseModel):
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_token_pair(user_id: str, username: str, roles: List[str], scopes: List[str] = None) -> TokenPair:
    """Create both access and refresh tokens"""
    token_data = {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "scopes": scopes or []
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user_id, "username": username})

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token
    )


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        roles: List[str] = payload.get("roles", [])
        scopes: List[str] = payload.get("scopes", [])

        if user_id is None or username is None:
            raise credentials_exception

        return TokenData(
            user_id=user_id,
            username=username,
            roles=roles,
            scopes=scopes
        )
    except JWTError:
        raise credentials_exception


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> TokenData:
    """FastAPI dependency to get current authenticated user"""
    token = credentials.credentials
    return decode_token(token)


def require_roles(required_roles: List[str]):
    """Decorator to require specific roles"""
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


def require_scopes(required_scopes: List[str]):
    """Decorator to require specific scopes"""
    async def scope_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not all(scope in current_user.scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scopes"
            )
        return current_user
    return scope_checker


# Role constants
class Roles:
    ADMIN = "admin"
    GESTIONNAIRE = "gestionnaire"
    AGENT_TERRAIN = "agent_terrain"
    COMPTABLE = "comptable"
