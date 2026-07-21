export interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

export interface ApiErrorDetail {
  field?: string;
  code?: string;
  message: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    request_id?: string;
    details?: ApiErrorDetail[];
  };
}

export interface BaseAuditMetadata {
  id: string;
  created_at: string;
  created_by?: {
    id: string;
    name: string;
  } | null;
  updated_at?: string | null;
  updated_by?: {
    id: string;
    name: string;
  } | null;
  deleted_at?: string | null;
  archived_at?: string | null;
  version?: number;
}
