// Auth & Users
export type Role = 'admin' | 'reviewer' | 'viewer';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

// Provider
export interface ProviderAlias {
  id: number;
  provider_id: number;
  alias_name: string;
  source: string;
  created_at: string;
}

export interface Provider {
  id: number;
  code: string;
  name: string;
  tax_id: string;
  address?: string;
  email?: string;
  phone?: string;
  is_active: boolean;
  aliases: ProviderAlias[];
  created_at: string;
  updated_at: string;
}

export interface CreateProviderRequest {
  code: string;
  name: string;
  tax_id: string;
  address?: string;
  email?: string;
  phone?: string;
}

// Document
export type DocumentStatus =
  | 'uploaded'
  | 'processing'
  | 'segmented'
  | 'ocr_done'
  | 'completed'
  | 'error';

export type SegmentStatus =
  | 'detected'
  | 'confirmed'
  | 'ocr_done'
  | 'extracted'
  | 'error';

export interface Page {
  id: number;
  document_id: number;
  page_number: number;
  image_path: string;
  thumbnail_path?: string;
  width?: number;
  height?: number;
}

export interface DetectedDoc {
  id: number;
  document_id: number;
  doc_type: string;
  page_start: number;
  page_end: number;
  confidence: number;
  status: SegmentStatus;
  invoice_id?: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  page_count: number;
  status: DocumentStatus;
  uploaded_by: number;
  upload_date: string;
  processed_at?: string;
  error_message?: string;
  pages: Page[];
  detected_docs: DetectedDoc[];
  created_at: string;
  updated_at: string;
}

export interface DocumentListItem {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  page_count: number;
  status: DocumentStatus;
  upload_date: string;
  uploaded_by: number;
  detected_count: number;
}

// Invoice
export type InvoiceStatus =
  | 'pending_review'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'exported';

export type LineStatus =
  | 'pending'
  | 'homologated'
  | 'manual'
  | 'rejected';

export interface InvoiceLineDestination {
  id: number;
  line_id: number;
  destination_id: number;
  quantity: number;
  destination?: Destination;
}

export interface InvoiceLine {
  id: number;
  invoice_id: number;
  line_number: number;
  supplier_code?: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  discount: number;
  subtotal: number;
  vat_rate: number;
  vat_amount: number;
  total: number;
  confidence: number;
  status: LineStatus;
  material_id?: number;
  material?: MaterialMaster;
  destinations: InvoiceLineDestination[];
  created_at: string;
  updated_at: string;
}

export interface Invoice {
  id: number;
  document_id: number;
  detected_doc_id?: number;
  provider_id?: number;
  provider?: Provider;
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  subtotal: number;
  vat_amount: number;
  total: number;
  currency: string;
  status: InvoiceStatus;
  confidence: number;
  reviewed_by?: number;
  reviewed_at?: string;
  rejection_reason?: string;
  lines: InvoiceLine[];
  created_at: string;
  updated_at: string;
}

export interface UpdateInvoiceHeaderRequest {
  provider_id?: number;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  subtotal?: number;
  vat_amount?: number;
  total?: number;
  currency?: string;
}

export interface UpdateInvoiceLineRequest {
  supplier_code?: string;
  description?: string;
  quantity?: number;
  unit?: string;
  unit_price?: number;
  discount?: number;
  subtotal?: number;
  vat_rate?: number;
  vat_amount?: number;
  total?: number;
}

export interface HomologateLineRequest {
  material_id: number;
  confirmed: boolean;
}

// Materials
export interface MaterialFamily {
  id: number;
  code: string;
  name: string;
  parent_id?: number;
}

export interface MaterialAlias {
  id: number;
  material_id: number;
  provider_id?: number;
  supplier_code?: string;
  alias_description: string;
  source: string;
  created_at: string;
}

export interface MaterialMaster {
  id: number;
  master_code: string;
  family_id?: number;
  family?: MaterialFamily;
  normalized_description: string;
  dimensions?: string;
  base_unit: string;
  is_active: boolean;
  aliases_count: number;
  aliases: MaterialAlias[];
  created_at: string;
  updated_at: string;
}

export interface CreateMaterialRequest {
  master_code: string;
  family_id?: number;
  normalized_description: string;
  dimensions?: string;
  base_unit: string;
}

export interface AddAliasRequest {
  provider_id?: number;
  supplier_code?: string;
  alias_description: string;
  source: string;
}

// Destination
export interface Destination {
  id: number;
  code: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateDestinationRequest {
  code: string;
  name: string;
  description?: string;
}

export interface AssignDestinationRequest {
  line_id: number;
  destination_id: number;
  quantity: number;
}

// Price History & Analytics
export interface PriceHistory {
  id: number;
  material_id: number;
  provider_id: number;
  provider?: Provider;
  invoice_id: number;
  invoice_date: string;
  unit_price: number;
  quantity: number;
  unit: string;
  currency: string;
}

export interface LastPriceResponse {
  material_id: number;
  material_code: string;
  material_description: string;
  provider_id: number;
  provider_name: string;
  last_price: number;
  last_date: string;
  currency: string;
}

export interface PriceHistoryPoint {
  date: string;
  price: number;
  provider_name: string;
  quantity: number;
}

export interface MaterialStats {
  material_id: number;
  master_code: string;
  normalized_description: string;
  total_spend: number;
  total_quantity: number;
  avg_price: number;
  invoice_count: number;
  currency: string;
}

export interface ProviderComparison {
  provider_id: number;
  provider_name: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  purchase_count: number;
  last_price: number;
  last_date: string;
}

export interface DashboardStats {
  total_invoices: number;
  pending_review: number;
  total_spent_this_month: number;
  pending_homologation: number;
  invoices_by_month: MonthlySpend[];
  spending_by_provider: ProviderSpend[];
  recent_documents: DocumentListItem[];
}

export interface MonthlySpend {
  month: string;
  total: number;
  count: number;
}

export interface ProviderSpend {
  provider_id: number;
  provider_name: string;
  total: number;
  percentage: number;
}

export interface SpendingByFamily {
  family_id: number;
  family_name: string;
  total: number;
  percentage: number;
}

// Audit
export interface AuditEvent {
  id: number;
  user_id: number;
  user?: User;
  entity_type: string;
  entity_id: number;
  action: string;
  old_values?: Record<string, unknown>;
  new_values?: Record<string, unknown>;
  created_at: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ListParams {
  page?: number;
  size?: number;
  search?: string;
  status?: string;
  provider_id?: number;
  family_id?: number;
  date_from?: string;
  date_to?: string;
}
