import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import MaterialMaster, Provider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_material(
    db: AsyncSession,
    master_code: str = "MAT-001",
    description: str = "Acero S275",
    family: str = "Aceros",
) -> MaterialMaster:
    material = MaterialMaster(
        master_code=master_code,
        normalized_description=description,
        family=family,
        active=True,
    )
    db.add(material)
    await db.flush()
    return material


async def _create_provider(
    db: AsyncSession,
    fiscal_name: str = "Proveedor SA",
    tax_id: str = "B12345678",
) -> Provider:
    provider = Provider(fiscal_name=fiscal_name, tax_id=tax_id, active=True)
    db.add(provider)
    await db.flush()
    return provider


# ---------------------------------------------------------------------------
# Material tests
# ---------------------------------------------------------------------------

async def test_create_material(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "master_code": "ACERO-001",
        "normalized_description": "Chapa acero S275 3mm",
        "family": "Chapas",
        "dimensions": "3mm",
    }
    response = await client.post("/materials", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["master_code"] == "ACERO-001"
    assert data["family"] == "Chapas"


async def test_get_material(client: AsyncClient, db_session: AsyncSession):
    material = await _create_material(db_session, master_code="MAT-GET")

    response = await client.get(f"/materials/{material.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == material.id
    assert data["master_code"] == "MAT-GET"


async def test_material_not_found(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/materials/999")
    assert response.status_code == 404


async def test_search_materials(client: AsyncClient, db_session: AsyncSession):
    await _create_material(db_session, master_code="ACERO-S275", description="Acero S275 tubo")
    await _create_material(db_session, master_code="ALUM-001", description="Aluminio perfil")

    response = await client.get("/materials/search?text=acero")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) >= 1
    codes = [r["master_code"] for r in results]
    assert "ACERO-S275" in codes


async def test_add_alias(client: AsyncClient, db_session: AsyncSession):
    material = await _create_material(db_session, master_code="MAT-ALIAS")
    provider = await _create_provider(db_session)

    payload = {
        "provider_id": provider.id,
        "supplier_code": "PROV-XYZ",
        "supplier_description": "Acero tubo proveedor",
        "confidence": 0.95,
    }
    response = await client.post(f"/materials/{material.id}/aliases", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["material_id"] == material.id
    assert data["supplier_code"] == "PROV-XYZ"


# ---------------------------------------------------------------------------
# Provider tests
# ---------------------------------------------------------------------------

async def test_create_provider(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "fiscal_name": "Suministros Industriales SL",
        "tax_id": "B87654321",
        "email": "info@suministros.com",
    }
    response = await client.post("/providers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["fiscal_name"] == "Suministros Industriales SL"
    assert data["tax_id"] == "B87654321"


async def test_get_provider(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(
        db_session, fiscal_name="Mi Proveedor", tax_id="A99999999"
    )

    response = await client.get(f"/providers/{provider.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == provider.id
    assert data["fiscal_name"] == "Mi Proveedor"


async def test_provider_not_found(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/providers/999")
    assert response.status_code == 404
