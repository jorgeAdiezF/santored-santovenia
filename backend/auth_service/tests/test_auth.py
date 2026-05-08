import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import hash_password, get_current_user
from shared.models import User, Role
from shared.database import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_role(db: AsyncSession, name: str = "admin") -> Role:
    role = Role(name=name, description=f"{name} role")
    db.add(role)
    await db.flush()
    return role


async def _create_user(
    db: AsyncSession,
    username: str = "alice",
    password: str = "secret123",
    role: Role | None = None,
    email: str | None = None,
    active: bool = True,
) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        name="Alice",
        email=email or f"{username}@example.com",
        active=active,
        role_id=role.id if role else None,
    )
    if role is not None:
        user.role = role
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    role = await _create_role(db_session)
    await _create_user(db_session, username="alice", password="secret123", role=role)

    response = await client.post(
        "/auth/login", json={"username": "alice", "password": "secret123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    role = await _create_role(db_session)
    await _create_user(db_session, username="bob", password="correct", role=role)

    response = await client.post(
        "/auth/login", json={"username": "bob", "password": "wrong"}
    )
    assert response.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/auth/login", json={"username": "ghost", "password": "nopass"}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

async def test_get_me(client: AsyncClient, db_session: AsyncSession):
    """The mock user injected by the fixture should be returned at /auth/me."""
    # The fixture overrides get_current_user to return a mock User with id=1.
    # We must have a matching row in the DB so the endpoint's selectinload works.
    role = await _create_role(db_session, name="admin")
    user = User(
        id=1,
        username="testuser",
        password_hash=hash_password("pass"),
        name="Test User",
        email="test@test.com",
        active=True,
        role_id=role.id,
    )
    user.role = role
    db_session.add(user)
    await db_session.flush()

    response = await client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"


# ---------------------------------------------------------------------------
# /users
# ---------------------------------------------------------------------------

async def test_list_users_as_admin(client: AsyncClient, db_session: AsyncSession):
    """GET /users should return a list (may be empty or contain created users)."""
    # The mock user from conftest has role "admin", so require_role("admin") passes.
    response = await client.get("/users")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_create_user(client: AsyncClient, db_session: AsyncSession):
    role = await _create_role(db_session, name="reviewer")

    payload = {
        "username": "newuser",
        "password": "pass1234",
        "name": "New User",
        "email": "newuser@example.com",
        "role_id": role.id,
    }
    response = await client.post("/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"


async def test_create_user_duplicate_username(
    client: AsyncClient, db_session: AsyncSession
):
    role = await _create_role(db_session, name="reviewer")
    await _create_user(db_session, username="dup", role=role)

    payload = {
        "username": "dup",
        "password": "anotherpass",
        "email": "other@example.com",
    }
    response = await client.post("/users", json=payload)
    assert response.status_code == 409


async def test_delete_user(client: AsyncClient, db_session: AsyncSession):
    role = await _create_role(db_session, name="reviewer")
    # Insert a placeholder user at id=1 first so the next user gets a different id
    # (the mock current_user has id=1 and the endpoint refuses self-deletion).
    placeholder = User(
        id=1,
        username="mockuser",
        password_hash=hash_password("x"),
        active=True,
    )
    db_session.add(placeholder)
    await db_session.flush()

    target = await _create_user(db_session, username="todelete", role=role)
    # target.id must differ from 1
    assert target.id != 1

    response = await client.delete(f"/users/{target.id}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
