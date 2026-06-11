"""
Tests for the Destinations Service HTTP endpoints.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Destination


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_destination(
    db: AsyncSession,
    name: str = "Almacén Central",
    description: str = "Almacén principal",
    active: bool = True,
) -> Destination:
    dest = Destination(name=name, description=description, active=active)
    db.add(dest)
    await db.flush()
    return dest


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_list_destinations_empty(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/destinations")
    assert response.status_code == 200
    data = response.json()
    # Endpoint returns a paginated envelope: {items, total, page, size, pages}
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_destinations(client: AsyncClient, db_session: AsyncSession):
    await _create_destination(db_session, name="Almacén A")
    await _create_destination(db_session, name="Almacén B")

    response = await client.get("/destinations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    names = [d["name"] for d in data["items"]]
    assert "Almacén A" in names
    assert "Almacén B" in names


async def test_list_destinations_excludes_inactive(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_destination(db_session, name="Activo", active=True)
    await _create_destination(db_session, name="Inactivo", active=False)

    # active_only=True is the default
    response = await client.get("/destinations")
    assert response.status_code == 200
    data = response.json()
    names = [d["name"] for d in data["items"]]
    assert "Activo" in names
    assert "Inactivo" not in names


async def test_create_destination(client: AsyncClient, db_session: AsyncSession):
    payload = {"name": "Obra Norte", "description": "Proyecto obras zona norte"}
    response = await client.post("/destinations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Obra Norte"
    assert data["active"] is True
    assert "id" in data


async def test_create_destination_duplicate(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_destination(db_session, name="Duplicado")
    payload = {"name": "Duplicado"}
    response = await client.post("/destinations", json=payload)
    assert response.status_code == 409


async def test_get_destination(client: AsyncClient, db_session: AsyncSession):
    dest = await _create_destination(db_session, name="Taller Principal")

    response = await client.get(f"/destinations/{dest.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dest.id
    assert data["name"] == "Taller Principal"


async def test_destination_not_found(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/destinations/999")
    assert response.status_code == 404


async def test_update_destination(client: AsyncClient, db_session: AsyncSession):
    dest = await _create_destination(db_session, name="Nombre Viejo")

    payload = {"name": "Nombre Nuevo", "description": "Descripción actualizada"}
    response = await client.put(f"/destinations/{dest.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Nombre Nuevo"
    assert data["description"] == "Descripción actualizada"


async def test_update_destination_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    payload = {"name": "No existe"}
    response = await client.put("/destinations/99999", json=payload)
    assert response.status_code == 404


async def test_delete_destination(client: AsyncClient, db_session: AsyncSession):
    """DELETE performs a soft-delete (sets active=False)."""
    dest = await _create_destination(db_session, name="Para Borrar")

    response = await client.delete(f"/destinations/{dest.id}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # The destination should no longer appear in active listing
    list_response = await client.get("/destinations")
    ids = [d["id"] for d in list_response.json()["items"]]
    assert dest.id not in ids


async def test_delete_destination_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.delete("/destinations/99999")
    assert response.status_code == 404
