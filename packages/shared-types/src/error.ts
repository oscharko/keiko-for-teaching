/**
 * Error types for the Keiko platform.
 */

export type ErrorCode =
  | 'VALIDATION_ERROR'
  | 'AUTHENTICATION_ERROR'
  | 'AUTHORIZATION_ERROR'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'RATE_LIMIT_EXCEEDED'
  | 'INTERNAL_SERVER_ERROR'
  | 'SERVICE_UNAVAILABLE'
  | 'BAD_REQUEST'
  | 'TIMEOUT';

export interface ErrorDetail {
  field?: string;
  message: string;
  code?: string;
}

export interface ApiError {
  error: string;
  code: ErrorCode;
  status_code: number;
  details?: ErrorDetail[];
  timestamp: string;
  request_id?: string;
  path?: string;
}

export interface ValidationError extends ApiError {
  code: 'VALIDATION_ERROR';
  details: ErrorDetail[];
}

export interface AuthenticationError extends ApiError {
  code: 'AUTHENTICATION_ERROR';
}

export interface AuthorizationError extends ApiError {
  code: 'AUTHORIZATION_ERROR';
}

export interface NotFoundError extends ApiError {
  code: 'NOT_FOUND';
}

export interface RateLimitError extends ApiError {
  code: 'RATE_LIMIT_EXCEEDED';
  retry_after?: number;
}

