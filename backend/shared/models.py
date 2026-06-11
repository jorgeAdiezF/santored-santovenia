from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Float, Numeric,
    Text, ForeignKey, BigInteger, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))
    name = Column(String(200))
    email = Column(String(200), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    active = Column(Boolean, default=True)

    role = relationship("Role", back_populates="users")
    documents = relationship("Document", back_populates="upload_user")
    validated_invoices = relationship("Invoice", back_populates="validated_by_user")
    audit_events = relationship("AuditEvent", back_populates="user")


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_name = Column(String(200), nullable=False)
    trade_name = Column(String(200))
    tax_id = Column(String(50), unique=True)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    active = Column(Boolean, default=True)

    aliases = relationship("ProviderAlias", back_populates="provider", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="provider")
    materials_aliases = relationship("MaterialAlias", back_populates="provider")
    price_history = relationship("PriceHistory", back_populates="provider")


class ProviderAlias(Base):
    __tablename__ = "provider_aliases"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id", ondelete="CASCADE"), nullable=False)
    alias_text = Column(String(300), nullable=False)

    provider = relationship("Provider", back_populates="aliases")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, nullable=False)
    filename = Column(String(300), nullable=False)
    file_type = Column(String(50))
    file_size = Column(BigInteger)
    storage_path = Column(String(500), nullable=False)
    upload_user_id = Column(Integer, ForeignKey("users.id"))
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="uploaded")
    page_count = Column(Integer)

    upload_user = relationship("User", back_populates="documents")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    detected_docs = relationship("DetectedDoc", back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(500), nullable=False)

    __table_args__ = (UniqueConstraint("document_id", "page_number"),)

    document = relationship("Document", back_populates="pages")
    invoice_lines = relationship("InvoiceLine", back_populates="page")


class DetectedDoc(Base):
    __tablename__ = "detected_docs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    start_page = Column(Integer, nullable=False)
    end_page = Column(Integer, nullable=False)
    status = Column(String(50), default="detected")
    confidence = Column(Float, default=0.0)

    document = relationship("Document", back_populates="detected_docs")
    invoice = relationship("Invoice", back_populates="detected_doc", uselist=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    detected_doc_id = Column(Integer, ForeignKey("detected_docs.id"))
    provider_id = Column(Integer, ForeignKey("providers.id"))
    tax_id = Column(String(50))
    invoice_number = Column(String(100))
    invoice_date = Column(Date)
    subtotal = Column(Numeric(15, 2))
    vat = Column(Numeric(15, 2))
    total = Column(Numeric(15, 2))
    currency = Column(String(10), default="EUR")
    status = Column(String(50), default="pending_review")
    validated_at = Column(DateTime(timezone=True))
    validated_by = Column(Integer, ForeignKey("users.id"))

    detected_doc = relationship("DetectedDoc", back_populates="invoice")
    provider = relationship("Provider", back_populates="invoices")
    validated_by_user = relationship("User", back_populates="validated_invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    supplier_code = Column(String(100))
    original_description = Column(Text)
    quantity = Column(Numeric(15, 4))
    unit = Column(String(50))
    unit_price = Column(Numeric(15, 4))
    discount = Column(Numeric(5, 2), default=0)
    subtotal = Column(Numeric(15, 2))
    tax_rate = Column(Numeric(5, 2), default=0)
    page_id = Column(Integer, ForeignKey("pages.id"))
    status = Column(String(50), default="pending_homologation")
    extraction_confidence = Column(Float, default=0.0)

    invoice = relationship("Invoice", back_populates="lines")
    page = relationship("Page", back_populates="invoice_lines")
    destinations = relationship("InvoiceLineDestination", back_populates="invoice_line", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="invoice_line")


class MaterialMaster(Base):
    __tablename__ = "materials_master"

    id = Column(Integer, primary_key=True, index=True)
    master_code = Column(String(100), unique=True, nullable=False)
    family = Column(String(100))
    subfamily = Column(String(100))
    normalized_description = Column(Text, nullable=False)
    dimensions = Column(String(200))
    thickness = Column(String(50))
    finish = Column(String(100))
    base_unit = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    aliases = relationship("MaterialAlias", back_populates="material", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="material")


class MaterialAlias(Base):
    __tablename__ = "materials_aliases"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials_master.id", ondelete="CASCADE"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    supplier_code = Column(String(100))
    supplier_description = Column(Text)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    material = relationship("MaterialMaster", back_populates="aliases")
    provider = relationship("Provider", back_populates="materials_aliases")


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)

    line_destinations = relationship("InvoiceLineDestination", back_populates="destination")


class InvoiceLineDestination(Base):
    __tablename__ = "invoice_line_destinations"

    id = Column(Integer, primary_key=True, index=True)
    invoice_line_id = Column(Integer, ForeignKey("invoice_lines.id", ondelete="CASCADE"), nullable=False)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    notes = Column(Text)

    __table_args__ = (UniqueConstraint("invoice_line_id", "destination_id"),)

    invoice_line = relationship("InvoiceLine", back_populates="destinations")
    destination = relationship("Destination", back_populates="line_destinations")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials_master.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    invoice_line_id = Column(Integer, ForeignKey("invoice_lines.id"))
    unit_price_original = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(50))
    unit_price_standard = Column(Numeric(15, 4))
    standard_unit = Column(String(50))
    quantity = Column(Numeric(15, 4))
    purchase_date = Column(Date, nullable=False)

    material = relationship("MaterialMaster", back_populates="price_history")
    provider = relationship("Provider", back_populates="price_history")
    invoice_line = relationship("InvoiceLine", back_populates="price_history")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    old_value = Column(JSON)
    new_value = Column(JSON)
    notes = Column(Text)

    user = relationship("User", back_populates="audit_events")
