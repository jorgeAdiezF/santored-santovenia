import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from shared.database import get_db
from shared.models import Destination, InvoiceLineDestination, InvoiceLine, User
from shared.auth import get_current_user
from shared.schemas import (
    DestinationCreate, DestinationUpdate, DestinationResponse,
    InvoiceLineDestinationCreate, InvoiceLineDestinationResponse,
    MessageResponse,
)
from shared.exceptions import NotFoundError, ConflictError
from shared.config import get_settings

settings = get_settings()

app = FastAPI(title="Destinations Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "destinations_service"}


@app.get("/destinations", response_model=List[DestinationResponse])
async def list_destinations(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Destination)
    if active_only:
        query = query.where(Destination.active == True)
    query = query.order_by(Destination.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.post("/destinations", response_model=DestinationResponse, status_code=status.HTTP_201_CREATED)
async def create_destination(
    destination_data: DestinationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(Destination).where(Destination.name == destination_data.name)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Destination '{destination_data.name}' already exists")

    destination = Destination(**destination_data.model_dump())
    db.add(destination)
    await db.flush()
    return destination


@app.get("/destinations/{destination_id}", response_model=DestinationResponse)
async def get_destination(
    destination_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Destination).where(Destination.id == destination_id)
    )
    destination = result.scalar_one_or_none()
    if not destination:
        raise NotFoundError("Destination", destination_id)
    return destination


@app.put("/destinations/{destination_id}", response_model=DestinationResponse)
async def update_destination(
    destination_id: int,
    destination_data: DestinationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Destination).where(Destination.id == destination_id)
    )
    destination = result.scalar_one_or_none()
    if not destination:
        raise NotFoundError("Destination", destination_id)

    for field, value in destination_data.model_dump(exclude_unset=True).items():
        setattr(destination, field, value)

    await db.flush()
    return destination


@app.delete("/destinations/{destination_id}", response_model=MessageResponse)
async def delete_destination(
    destination_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Destination).where(Destination.id == destination_id)
    )
    destination = result.scalar_one_or_none()
    if not destination:
        raise NotFoundError("Destination", destination_id)

    destination.active = False
    await db.flush()
    return MessageResponse(message=f"Destination {destination_id} deactivated")


@app.post(
    "/invoice-lines/{line_id}/destinations",
    response_model=InvoiceLineDestinationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_destination(
    line_id: int,
    assignment_data: InvoiceLineDestinationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InvoiceLine).where(InvoiceLine.id == line_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("InvoiceLine", line_id)

    result = await db.execute(
        select(Destination).where(
            Destination.id == assignment_data.destination_id,
            Destination.active == True,
        )
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("Destination", assignment_data.destination_id)

    existing = await db.execute(
        select(InvoiceLineDestination).where(
            InvoiceLineDestination.invoice_line_id == line_id,
            InvoiceLineDestination.destination_id == assignment_data.destination_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Destination already assigned to this line")

    assignment = InvoiceLineDestination(
        invoice_line_id=line_id,
        destination_id=assignment_data.destination_id,
        notes=assignment_data.notes,
    )
    db.add(assignment)
    await db.flush()

    result = await db.execute(
        select(InvoiceLineDestination)
        .options(selectinload(InvoiceLineDestination.destination))
        .where(InvoiceLineDestination.id == assignment.id)
    )
    return result.scalar_one()


@app.get(
    "/invoice-lines/{line_id}/destinations",
    response_model=List[InvoiceLineDestinationResponse],
)
async def get_line_destinations(
    line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InvoiceLine).where(InvoiceLine.id == line_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("InvoiceLine", line_id)

    result = await db.execute(
        select(InvoiceLineDestination)
        .options(selectinload(InvoiceLineDestination.destination))
        .where(InvoiceLineDestination.invoice_line_id == line_id)
    )
    return result.scalars().all()


@app.delete("/invoice-line-destinations/{assignment_id}", response_model=MessageResponse)
async def remove_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InvoiceLineDestination).where(InvoiceLineDestination.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment", assignment_id)

    await db.delete(assignment)
    await db.flush()
    return MessageResponse(message=f"Assignment {assignment_id} removed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
