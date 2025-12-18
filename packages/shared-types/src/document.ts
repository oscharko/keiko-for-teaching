/**
 * Document types for the Keiko document service.
 */

export type DocumentStatus = 'uploaded' | 'processing' | 'indexed' | 'failed';

export interface DocumentMetadata {
  id: string;
  filename: string;
  content_type: string;
  size: number;
  uploaded_at: string;
  uploaded_by?: string;
  status: DocumentStatus;
  blob_url?: string;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  size: number;
  status: DocumentStatus;
  message: string;
}

export interface DocumentListResponse {
  documents: DocumentMetadata[];
  total_count: number;
}

export interface DocumentDeleteResponse {
  status: string;
  message: string;
}

