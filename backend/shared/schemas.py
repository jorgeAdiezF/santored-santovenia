from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal


# --- Role ---
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --- User ---
class UserCreate(BaseModel):
    username: str
    password: str
    role_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    active: bool
    role: Optional[RoleResponse] = None


# --- Auth ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Provider ---
class ProviderCreate(BaseModel):
    fiscal_name: str
    trade_name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ProviderUpdate(BaseModel):
    fiscal_name: Optional[str] = None
    trade_name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    active: Optional[bool] = None


class ProviderAliasCreate(BaseModel):
    alias_text: str


class ProviderAliasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    provider_id: int
    alias_text: str


class ProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fiscal_name: str
    trade_name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    active: bool
    aliases: List[ProviderAliasResponse] = []


# --- Document ---
class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_hash: str
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    storage_path: str
    upload_user_id: Optional[int] = None
    upload_date: Optional[datetime] = None
    status: str
    page_count: Optional[int] = None


class PageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    page_number: int
    image_path: str


# --- Detected Docs (Segments) ---
class DetectedDocResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    start_page: int
    end_page: int
    status: str
    confidence: float


class DetectedDocUpdate(BaseModel):
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    status: Optional[str] = None


class SegmentMergeRequest(BaseModel):
    segment_id_1: int
    segment_id_2: int


class SegmentSplitRequest(BaseModel):
    split_at_page: int


# --- Invoice ---
class InvoiceUpdate(BaseModel):
    provider_id: Optional[int] = None
    tax_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    vat: Optional[Decimal] = None
    total: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    detected_doc_id: Optional[int] = None
    provider_id: Optional[int] = None
    tax_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    vat: Optional[Decimal] = None
    total: Optional[Decimal] = None
    currency: str
    status: str
    validated_at: Optional[datetime] = None
    validated_by: Optional[int] = None


# --- Invoice Line ---
class InvoiceLineUpdate(BaseModel):
    supplier_code: Optional[str] = None
    original_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    status: Optional[str] = None


class InvoiceLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_id: int
    line_number: int
    supplier_code: Optional[str] = None
    original_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    page_id: Optional[int] = None
    status: str
    extraction_confidence: float


# --- Material ---
class MaterialCreate(BaseModel):
    master_code: str
    family: Optional[str] = None
    subfamily: Optional[str] = None
    normalized_description: str
    dimensions: Optional[str] = None
    thickness: Optional[str] = None
    finish: Optional[str] = None
    base_unit: Optional[str] = None


class MaterialUpdate(BaseModel):
    master_code: Optional[str] = None
    family: Optional[str] = None
    subfamily: Optional[str] = None
    normalized_description: Optional[str] = None
    dimensions: Optional[str] = None
    thickness: Optional[str] = None
    finish: Optional[str] = None
    base_unit: Optional[str] = None
    active: Optional[bool] = None


class MaterialAliasCreate(BaseModel):
    provider_id: Optional[int] = None
    supplier_code: Optional[str] = None
    supplier_description: Optional[str] = None
    confidence: Optional[float] = 1.0


class MaterialAliasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    material_id: int
    provider_id: Optional[int] = None
    supplier_code: Optional[str] = None
    supplier_description: Optional[str] = None
    confidence: float
    created_at: Optional[datetime] = None


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    master_code: str
    family: Optional[str] = None
    subfamily: Optional[str] = None
    normalized_description: str
    dimensions: Optional[str] = None
    thickness: Optional[str] = None
    finish: Optional[str] = None
    base_unit: Optional[str] = None
    active: bool
    created_at: Optional[datetime] = None
    aliases: List[MaterialAliasResponse] = []


# --- Destination ---
class DestinationCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DestinationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class DestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    active: bool


class InvoiceLineDestinationCreate(BaseModel):
    destination_id: int
    notes: Optional[str] = None


class InvoiceLineDestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_line_id: int
    destination_id: int
    notes: Optional[str] = None
    destination: Optional[DestinationResponse] = None


# --- Price History ---
class PriceHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    material_id: int
    provider_id: int
    invoice_line_id: Optional[int] = None
    unit_price_original: Decimal
    unit: Optional[str] = None
    unit_price_standard: Optional[Decimal] = None
    standard_unit: Optional[str] = None
    quantity: Optional[Decimal] = None
    purchase_date: date


# --- Analytics ---
class LastPriceResponse(BaseModel):
    material_id: int
    provider_id: int
    provider_name: str
    material_description: str
    unit_price_standard: Optional[Decimal] = None
    standard_unit: Optional[str] = None
    purchase_date: date


class DashboardResponse(BaseModel):
    total_invoices: int
    pending_review: int
    validated_this_month: int
    total_spend_this_month: Optional[Decimal] = None
    pending_homologation_lines: int


class SpendingByProviderResponse(BaseModel):
    provider_id: int
    provider_name: str
    total_spend: Decimal
    invoice_count: int


class SpendingByFamilyResponse(BaseModel):
    family: str
    total_spend: Decimal
    line_count: int


# --- Homologation ---
class HomologationSuggestion(BaseModel):
    material_id: int
    master_code: str
    normalized_description: str
    family: Optional[str] = None
    confidence: float


class HomologationAssign(BaseModel):
    material_id: int
    confidence: Optional[float] = 1.0


# --- Generic ---
class MessageResponse(BaseModel):
    message: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
