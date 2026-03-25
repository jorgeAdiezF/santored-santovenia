import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from shared.database import get_db
from shared.models import MaterialMaster, MaterialAlias, Provider, ProviderAlias, User
from shared.auth import get_current_user
from shared.schemas import (
    MaterialCreate, MaterialUpdate, MaterialResponse, MaterialAliasCreate, MaterialAliasResponse,
    ProviderCreate, ProviderUpdate, ProviderResponse, ProviderAliasCreate, ProviderAliasResponse,
    MessageResponse,
)
from shared.exceptions import NotFoundError, ConflictError
from shared.config import get_settings

settings = get_settings()

app = FastAPI(title="Materials Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "materials_service"}


# ---- Materials endpoints ----

@app.get("/materials/search", response_model=List[MaterialResponse])
async def search_materials(
    text: Optional[str] = Query(None),
    family: Optional[str] = Query(None),
    subfamily: Optional[str] = Query(None),
    dimensions: Optional[str] = Query(None),
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(MaterialMaster).options(selectinload(MaterialMaster.aliases))

    if active_only:
        query = query.where(MaterialMaster.active == True)
    if text:
        query = query.where(
            or_(
                MaterialMaster.normalized_description.ilike(f"%{text}%"),
                MaterialMaster.master_code.ilike(f"%{text}%"),
            )
        )
    if family:
        query = query.where(MaterialMaster.family.ilike(f"%{family}%"))
    if subfamily:
        query = query.where(MaterialMaster.subfamily.ilike(f"%{subfamily}%"))
    if dimensions:
        query = query.where(MaterialMaster.dimensions.ilike(f"%{dimensions}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/materials/families", response_model=List[str])
async def list_families(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MaterialMaster.family).where(
            MaterialMaster.family.isnot(None),
            MaterialMaster.active == True,
        ).distinct()
    )
    return [row[0] for row in result.all() if row[0]]


@app.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    material_data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(MaterialMaster).where(MaterialMaster.master_code == material_data.master_code)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Material with code '{material_data.master_code}' already exists")

    material = MaterialMaster(**material_data.model_dump())
    db.add(material)
    await db.flush()

    result = await db.execute(
        select(MaterialMaster).options(selectinload(MaterialMaster.aliases)).where(MaterialMaster.id == material.id)
    )
    return result.scalar_one()


@app.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MaterialMaster).options(selectinload(MaterialMaster.aliases)).where(MaterialMaster.id == material_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise NotFoundError("Material", material_id)
    return material


@app.put("/materials/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MaterialMaster).where(MaterialMaster.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise NotFoundError("Material", material_id)

    for field, value in material_data.model_dump(exclude_unset=True).items():
        setattr(material, field, value)

    await db.flush()

    result = await db.execute(
        select(MaterialMaster).options(selectinload(MaterialMaster.aliases)).where(MaterialMaster.id == material_id)
    )
    return result.scalar_one()


@app.delete("/materials/{material_id}", response_model=MessageResponse)
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MaterialMaster).where(MaterialMaster.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise NotFoundError("Material", material_id)

    material.active = False
    await db.flush()
    return MessageResponse(message=f"Material {material_id} deactivated")


@app.get("/materials/{material_id}/aliases", response_model=List[MaterialAliasResponse])
async def get_material_aliases(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MaterialMaster).where(MaterialMaster.id == material_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("Material", material_id)

    result = await db.execute(
        select(MaterialAlias).where(MaterialAlias.material_id == material_id)
    )
    return result.scalars().all()


@app.post("/materials/{material_id}/aliases", response_model=MaterialAliasResponse, status_code=status.HTTP_201_CREATED)
async def add_material_alias(
    material_id: int,
    alias_data: MaterialAliasCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(MaterialMaster).where(MaterialMaster.id == material_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("Material", material_id)

    alias = MaterialAlias(material_id=material_id, **alias_data.model_dump())
    db.add(alias)
    await db.flush()
    return alias


@app.delete("/materials/{material_id}/aliases/{alias_id}", response_model=MessageResponse)
async def remove_material_alias(
    material_id: int,
    alias_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MaterialAlias).where(
            MaterialAlias.id == alias_id,
            MaterialAlias.material_id == material_id,
        )
    )
    alias = result.scalar_one_or_none()
    if not alias:
        raise NotFoundError("Alias", alias_id)

    await db.delete(alias)
    await db.flush()
    return MessageResponse(message=f"Alias {alias_id} removed")


# ---- Providers endpoints ----

@app.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Provider).options(selectinload(Provider.aliases))
    if active_only:
        query = query.where(Provider.active == True)
    if search:
        query = query.where(
            or_(
                Provider.fiscal_name.ilike(f"%{search}%"),
                Provider.tax_id.ilike(f"%{search}%"),
            )
        )
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/providers", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if provider_data.tax_id:
        existing = await db.execute(
            select(Provider).where(Provider.tax_id == provider_data.tax_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Provider with tax_id '{provider_data.tax_id}' already exists")

    provider = Provider(**provider_data.model_dump())
    db.add(provider)
    await db.flush()

    result = await db.execute(
        select(Provider).options(selectinload(Provider.aliases)).where(Provider.id == provider.id)
    )
    return result.scalar_one()


@app.get("/providers/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Provider).options(selectinload(Provider.aliases)).where(Provider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise NotFoundError("Provider", provider_id)
    return provider


@app.put("/providers/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: int,
    provider_data: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise NotFoundError("Provider", provider_id)

    for field, value in provider_data.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)

    await db.flush()

    result = await db.execute(
        select(Provider).options(selectinload(Provider.aliases)).where(Provider.id == provider_id)
    )
    return result.scalar_one()


@app.get("/providers/{provider_id}/aliases", response_model=List[ProviderAliasResponse])
async def get_provider_aliases(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Provider).where(Provider.id == provider_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("Provider", provider_id)

    result = await db.execute(
        select(ProviderAlias).where(ProviderAlias.provider_id == provider_id)
    )
    return result.scalars().all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
