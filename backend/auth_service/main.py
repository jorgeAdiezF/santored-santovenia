import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import timedelta

from shared.database import get_db
from shared.models import User, Role
from shared.auth import (
    verify_password, hash_password, create_access_token,
    create_refresh_token, decode_token, get_current_user, require_role
)
from shared.schemas import (
    LoginRequest, TokenResponse, RefreshRequest, UserCreate, UserUpdate,
    UserResponse, MessageResponse
)
from shared.exceptions import NotFoundError, ConflictError, UnauthorizedError
from shared.config import get_settings
from shared.audit import record_audit

settings = get_settings()

app = FastAPI(title="Auth Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth_service"}


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    token_data = {"sub": str(user.id), "username": user.username}
    if user.role:
        token_data["role"] = user.role.name

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(request.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError()

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if not user or not user.active:
        raise UnauthorizedError("User not found or inactive")

    token_data = {"sub": str(user.id), "username": user.username}
    if user.role:
        token_data["role"] = user.role.name

    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@app.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", current_user.id)
    return user


@app.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    query = select(User).options(selectinload(User.role))
    if active_only:
        query = query.where(User.active == True)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise ConflictError(f"Username '{user_data.username}' already exists")

    if user_data.email:
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise ConflictError(f"Email '{user_data.email}' already registered")

    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role_id=user_data.role_id,
        name=user_data.name,
        email=user_data.email,
        active=True,
    )
    db.add(new_user)
    await db.flush()

    await record_audit(db, "create", "user", new_user.id, current_user.id,
                       new_value={"username": new_user.username, "email": new_user.email})

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == new_user.id)
    )
    return result.scalar_one()


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_id)
    return user


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_id)

    if user_data.username is not None:
        existing = await db.execute(
            select(User).where(User.username == user_data.username, User.id != user_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Username '{user_data.username}' already taken")
        user.username = user_data.username

    if user_data.password is not None:
        user.password_hash = hash_password(user_data.password)
    if user_data.role_id is not None:
        user.role_id = user_data.role_id
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.active is not None:
        user.active = user_data.active

    await db.flush()
    await record_audit(db, "update", "user", user_id, current_user.id,
                       new_value=user_data.model_dump(exclude_unset=True, exclude={"password"}))

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    return result.scalar_one()


@app.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_id)

    user.active = False
    await db.flush()
    await record_audit(db, "delete", "user", user_id, current_user.id,
                       old_value={"username": user.username})

    return MessageResponse(message=f"User {user_id} deactivated successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
