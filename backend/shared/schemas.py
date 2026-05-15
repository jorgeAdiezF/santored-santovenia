from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field, field_validator
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

    # Frontend compatibility aliases
    @computed_field
    @property
    def name(self) -> str:
        return self.fiscal_name

    @computed_field
    @property
    def code(self) -> str:
        return self.tax_id or ""

    @computed_field
    @property
    def is_active(self) -> bool:
        return self.active

    @computed_field
    @property
    def updated_at(self) -> Optional[datetime]:
        return self.created_at


# --- Document ---
class PageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    page_number: int
    image_path: str


class DetectedDocResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    start_page: int
    end_page: int
    status: str
    confidence: float

    # Frontend compatibility aliases
    @computed_field
    @property
    def page_start(self) -> int:
        return self.start_page

    @computed_field
    @property
    def page_end(self) -> int:
        return self.end_page

    @computed_field
    @property
    def doc_type(self) -> str:
        return "invoice"

    @computed_field
    @property
    def created_at(self) -> Optional[str]:
        return None

    @computed_field
    @property
    def updated_at(self) -> Optional[str]:
        return None


class DetectedDocUpdate(BaseModel):
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    status: Optional[str] = None


class SegmentMergeRequest(BaseModel):
    segment_id_1: int
    segment_id_2: int


class SegmentSplitRequest(BaseModel):
    split_at_page: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    storage_path: str = ""
    upload_user_id: Optional[int] = None
    upload_date: Optional[datetime] = None
    status: str
    page_count: Optional[int] = None
    pages: List[PageResponse] = []
    detected_docs: List[DetectedDocResponse] = []
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @field_validator('status', mode='before')
    @classmethod
    def normalize_doc_status(cls, v: Any) -> str:
        if v == 'pages_extracted':
            return 'processing'
        return str(v) if v is not None else 'uploaded'

    # Frontend compatibility aliases
    @computed_field
    @property
    def original_filename(self) -> str:
        return self.filename

    @computed_field
    @property
    def file_path(self) -> str:
        return self.storage_path

    @computed_field
    @property
    def uploaded_by(self) -> Optional[int]:
        return self.upload_user_id

    @computed_field
    @property
    def created_at(self) -> Optional[datetime]:
        return self.upload_date

    @computed_field
    @property
    def updated_at(self) -> Optional[datetime]:
        return self.upload_date


class DocumentListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    status: str
    upload_date: Optional[datetime] = None
    upload_user_id: Optional[int] = None
    detected_docs: List[DetectedDocResponse] = []

    @field_validator('status', mode='before')
    @classmethod
    def normalize_doc_status(cls, v: Any) -> str:
        if v == 'pages_extracted':
            return 'processing'
        return str(v) if v is not None else 'uploaded'

    @computed_field
    @property
    def original_filename(self) -> str:
        return self.filename

    @computed_field
    @property
    def uploaded_by(self) -> Optional[int]:
        return self.upload_user_id

    @computed_field
    @property
    def created_at(self) -> Optional[datetime]:
        return self.upload_date

    @computed_field
    @property
    def detected_count(self) -> int:
        return len(self.detected_docs)


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


class InvoiceLineDestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_line_id: int
    destination_id: int
    notes: Optional[str] = None

    @computed_field
    @property
    def line_id(self) -> int:
        return self.invoice_line_id

    @computed_field
    @property
    def quantity(self) -> float:
        return 0.0


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
    destinations: List[InvoiceLineDestinationResponse] = []

    @field_validator('status', mode='before')
    @classmethod
    def normalize_line_status(cls, v: Any) -> str:
        mapping = {
            'pending_homologation': 'pending',
            'pending_review': 'pending',
            'no_match': 'pending',
        }
        return mapping.get(str(v), str(v)) if v is not None else 'pending'

    # Frontend compatibility aliases
    @computed_field
    @property
    def description(self) -> Optional[str]:
        return self.original_description

    @computed_field
    @property
    def vat_rate(self) -> Optional[Decimal]:
        return self.tax_rate

    @computed_field
    @property
    def confidence(self) -> float:
        return self.extraction_confidence

    @computed_field
    @property
    def vat_amount(self) -> Optional[Decimal]:
        if self.subtotal is not None and self.tax_rate is not None:
            return (self.subtotal * self.tax_rate / 100).quantize(Decimal('0.01'))
        return None

    @computed_field
    @property
    def total(self) -> Optional[Decimal]:
        if self.subtotal is not None:
            vat = self.vat_amount or Decimal('0')
            return self.subtotal + vat
        return None

    @computed_field
    @property
    def material_id(self) -> Optional[int]:
        return None

    @computed_field
    @property
    def created_at(self) -> Optional[str]:
        return None

    @computed_field
    @property
    def updated_at(self) -> Optional[str]:
        return None


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
    provider: Optional[ProviderResponse] = None
    lines: List[InvoiceLineResponse] = []

    @field_validator('status', mode='before')
    @classmethod
    def normalize_invoice_status(cls, v: Any) -> str:
        mapping = {
            'validated': 'approved',
            'under_review': 'under_review',
        }
        return mapping.get(str(v), str(v)) if v is not None else 'pending_review'

    # Frontend compatibility aliases
    @computed_field
    @property
    def vat_amount(self) -> Optional[Decimal]:
        return self.vat

    @computed_field
    @property
    def reviewed_by(self) -> Optional[int]:
        return self.validated_by

    @computed_field
    @property
    def reviewed_at(self) -> Optional[datetime]:
        return self.validated_at

    @computed_field
    @property
    def confidence(self) -> float:
        return 0.0

    @computed_field
    @property
    def document_id(self) -> Optional[int]:
        return None

    @computed_field
    @property
    def due_date(self) -> Optional[date]:
        return None

    @computed_field
    @property
    def rejection_reason(self) -> Optional[str]:
        return None

    @computed_field
    @property
    def created_at(self) -> Optional[datetime]:
        return self.validated_at

    @computed_field
    @property
    def updated_at(self) -> Optional[datetime]:
        return self.validated_at


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

    @computed_field
    @property
    def code(self) -> str:
        return str(self.id)

    @computed_field
    @property
    def is_active(self) -> bool:
        return self.active

    @computed_field
    @property
    def created_at(self) -> Optional[str]:
        return None

    @computed_field
    @property
    def updated_at(self) -> Optional[str]:
        return None


class InvoiceLineDestinationCreate(BaseModel):
    destination_id: int
    quantity: Optional[float] = None
    notes: Optional[str] = None


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
