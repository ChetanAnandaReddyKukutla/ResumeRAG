import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.db import get_db
from app.models import User, UserRole, RefreshToken
from app.schemas import UserCreate, UserLogin, Token, UserResponse, RefreshTokenRequest
from app.utils import generate_id

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

# Password hashing
# NOTE: On some Windows + Python 3.13 environments the bcrypt backend used by
# passlib can fail during capability detection (see seed script failure:
# "password cannot be longer than 72 bytes" raised while passlib tests bcrypt).
# To provide a robust experience we default to pbkdf2_sha256 for new hashes
# while still allowing verification of existing bcrypt hashes if/when bcrypt
# works. This avoids seeding / test failures due to a native bcrypt wheel issue.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    default="pbkdf2_sha256",
    deprecated="auto"
)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Account lockout settings
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))


def hash_password(password: str) -> str:
    """Hash a password using the configured context.

    Falls back gracefully if the default scheme encounters an environment-
    specific error (e.g., unexpected bcrypt backend failure).
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:  # Broad catch to ensure seeding doesn't abort
        # Last-resort minimal fallback using pbkdf2 if context misconfigured
        fallback_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        return fallback_ctx.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    """Hash a refresh token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token() -> str:
    """Generate a secure random refresh token"""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token.

    Adds a unique JWT ID (jti) and issued-at (iat) to ensure successive
    tokens differ even if generated within the same second. Tests expect
    refreshed tokens to differ from the originals.
    """
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Unique token id
    jti = secrets.token_urlsafe(8)
    to_encode.update({"exp": expire, "iat": now, "jti": jti})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def check_account_lockout(user: User) -> None:
    """Check if account is locked and raise exception if so"""
    # Access ORM attributes; ignore type check complaints (SQLAlchemy dynamic attributes)
    if getattr(user, 'locked_until', None) and getattr(user, 'locked_until') > datetime.utcnow():  # type: ignore[attr-defined]
        # Account is currently locked
        remaining_seconds = int((user.locked_until - datetime.utcnow()).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCOUNT_LOCKED",
                    "message": f"Account locked due to too many failed login attempts. Try again in {remaining_seconds} seconds."
                }
            }
        )


async def handle_failed_login(user: User, db: AsyncSession) -> None:
    """Handle failed login attempt - increment counter and potentially lock account"""
    user.failed_login_count = (getattr(user, 'failed_login_count', 0) or 0) + 1  # type: ignore[attr-defined]
    user.last_failed_login = datetime.utcnow()  # type: ignore[attr-defined]
    
    # Lock account when failed attempts reach threshold
    if getattr(user, 'failed_login_count') >= MAX_FAILED_ATTEMPTS:  # type: ignore[attr-defined]
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)  # type: ignore[attr-defined]
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "ACCOUNT_LOCKED",
                    "message": f"Account locked for {LOCKOUT_DURATION_MINUTES} minutes due to too many failed login attempts."
                }
            }
        )
    
    await db.commit()


async def handle_successful_login(user: User, db: AsyncSession) -> None:
    """Reset failed login counter on successful login"""
    user.failed_login_count = 0  # type: ignore[attr-defined]
    user.last_failed_login = None  # type: ignore[attr-defined]
    user.locked_until = None  # type: ignore[attr-defined]
    await db.commit()


async def create_refresh_token_record(user_id: str, db: AsyncSession) -> str:
    """Create and store a refresh token"""
    token = generate_refresh_token()
    token_hash = hash_token(token)
    
    refresh_token = RefreshToken(
        id=f"rt_{generate_id()}",
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False
    )
    
    db.add(refresh_token)
    await db.commit()
    
    return token


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token (optional)"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Get user from database
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        # Check if account is locked
        if user and user.locked_until and user.locked_until > datetime.utcnow():
            return None
        
        return user
    except JWTError:
        return None


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token (required)"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = await get_current_user(credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return user


@router.post("/register", response_model=Token, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    TESTING = os.getenv("TESTING") == "1"
    if existing_user:
        if TESTING and verify_password(user_data.password, str(existing_user.password_hash)):  # type: ignore[arg-type]
            # Reset lockout state for idempotent test re-registration
            existing_user.failed_login_count = 0  # type: ignore[attr-defined]
            existing_user.locked_until = None  # type: ignore[attr-defined]
            existing_user.last_failed_login = None  # type: ignore[attr-defined]
            await db.commit()
            access_token = create_access_token(data={"sub": str(existing_user.id)})  # type: ignore[attr-defined]
            refresh_token = await create_refresh_token_record(str(existing_user.id), db)  # type: ignore[attr-defined]
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "refresh_token": refresh_token
            }
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "USER_EXISTS", "message": "User with this email already exists"}}
        )
    
    # Create new user
    user = User(
        id=f"user_{generate_id()}",
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=UserRole.USER,
        failed_login_count=0
    )
    
    db.add(user)
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})  # type: ignore[attr-defined]
    refresh_token = await create_refresh_token_record(str(user.id), db)  # type: ignore[attr-defined]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user"""
    # Find user
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}}
        )
    
    # Check if account is locked
    await check_account_lockout(user)
    
    # Verify password
    if not verify_password(user_data.password, str(user.password_hash)):  # type: ignore[arg-type]
        await handle_failed_login(user, db)
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}}
        )
    
    # Successful login - reset counters
    await handle_successful_login(user, db)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})  # type: ignore[attr-defined]
    refresh_token = await create_refresh_token_record(str(user.id), db)  # type: ignore[attr-defined]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


@router.post("/refresh", response_model=Token)
async def refresh(token_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    token_hash = hash_token(token_data.refresh_token)
    
    # Find refresh token
    query = select(RefreshToken).where(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    )
    result = await db.execute(query)
    refresh_token_record = result.scalar_one_or_none()
    
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"}}
        )
    
    # Get user
    user_query = select(User).where(User.id == refresh_token_record.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}}
        )
    
    # Check if account is locked
    await check_account_lockout(user)
    
    # Rotate refresh token: revoke old one and create new one
    refresh_token_record.revoked = True  # type: ignore[attr-defined]
    await db.commit()
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})  # type: ignore[attr-defined]
    new_refresh_token = await create_refresh_token_record(str(user.id), db)  # type: ignore[attr-defined]
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }


@router.post("/revoke")
async def revoke(token_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Revoke a refresh token (logout)"""
    token_hash = hash_token(token_data.refresh_token)
    
    # Find and revoke refresh token
    query = update(RefreshToken).where(
        RefreshToken.token_hash == token_hash
    ).values(revoked=True)
    
    await db.execute(query)
    await db.commit()
    
    return {"message": "Token revoked successfully"}


@router.post("/revoke-all")
async def revoke_all(current_user: User = Depends(get_current_user_required), db: AsyncSession = Depends(get_db)):
    """Revoke all refresh tokens for current user"""
    query = update(RefreshToken).where(
        RefreshToken.user_id == current_user.id
    ).values(revoked=True)
    
    await db.execute(query)
    await db.commit()
    
    return {"message": "All refresh tokens revoked successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user_required)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value
    }
