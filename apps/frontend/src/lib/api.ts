import type { ChatRequest, ChatResponse } from '@keiko/shared-types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Error class with enhanced error handling
class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Request interceptor type
type RequestInterceptor = (config: RequestInit) => RequestInit | Promise<RequestInit>;

// Response interceptor type
type ResponseInterceptor = <T>(response: Response, data: T) => T | Promise<T>;

// Global interceptors
const requestInterceptors: RequestInterceptor[] = [];
const responseInterceptors: ResponseInterceptor[] = [];

// Add request interceptor
export function addRequestInterceptor(interceptor: RequestInterceptor): void {
  requestInterceptors.push(interceptor);
}

// Add response interceptor
export function addResponseInterceptor(interceptor: ResponseInterceptor): void {
  responseInterceptors.push(interceptor);
}

// Get auth token (can be customized)
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

// Retry configuration
interface RetryConfig {
  maxRetries?: number;
  retryDelay?: number;
  retryableStatuses?: number[];
}

const defaultRetryConfig: Required<RetryConfig> = {
  maxRetries: 3,
  retryDelay: 1000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

// Sleep utility for retry delay
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Enhanced fetchApi with interceptors, retry logic, and better error handling
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  retryConfig: RetryConfig = {}
): Promise<T> {
  const config = { ...defaultRetryConfig, ...retryConfig };
  let lastError: ApiError | null = null;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      // Apply request interceptors
      let requestOptions = { ...options };
      for (const interceptor of requestInterceptors) {
        requestOptions = await interceptor(requestOptions);
      }

      // Add auth token if available
      const token = getAuthToken();
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...requestOptions.headers,
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...requestOptions,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const apiError = new ApiError(
          response.status,
          errorData.code || 'UNKNOWN_ERROR',
          errorData.error || errorData.message || 'An error occurred',
          errorData.details
        );

        // Check if we should retry
        if (
          attempt < config.maxRetries &&
          config.retryableStatuses.includes(response.status)
        ) {
          lastError = apiError;
          await sleep(config.retryDelay * (attempt + 1)); // Exponential backoff
          continue;
        }

        throw apiError;
      }

      let data = await response.json();

      // Apply response interceptors
      for (const interceptor of responseInterceptors) {
        data = await interceptor(response, data);
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        lastError = error;

        // Don't retry if it's not a retryable status
        if (!config.retryableStatuses.includes(error.status)) {
          throw error;
        }
      } else {
        // Network error or other unexpected error
        throw new ApiError(
          0,
          'NETWORK_ERROR',
          error instanceof Error ? error.message : 'Network error occurred',
          error
        );
      }

      // If this was the last attempt, throw the error
      if (attempt === config.maxRetries) {
        throw lastError;
      }

      // Wait before retrying
      await sleep(config.retryDelay * (attempt + 1));
    }
  }

  // This should never be reached, but TypeScript needs it
  throw lastError || new ApiError(0, 'UNKNOWN_ERROR', 'Unknown error occurred');
}

// Enhanced streaming support with better error handling
async function* streamApi<T>(
  endpoint: string,
  options: RequestInit = {}
): AsyncGenerator<T, void, unknown> {
  // Apply request interceptors
  let requestOptions = { ...options };
  for (const interceptor of requestInterceptors) {
    requestOptions = await interceptor(requestOptions);
  }

  // Add auth token if available
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...requestOptions.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...requestOptions,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.code || 'STREAM_ERROR',
      errorData.error || 'Failed to stream',
      errorData.details
    );
  }

  if (!response.body) {
    throw new ApiError(500, 'NO_BODY', 'Response body is empty');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;

        if (trimmedLine.startsWith('data: ')) {
          const dataStr = trimmedLine.slice(6);

          // Handle [DONE] signal
          if (dataStr === '[DONE]') {
            return;
          }

          try {
            const data = JSON.parse(dataStr);
            yield data as T;
          } catch (parseError) {
            console.error('Failed to parse SSE data:', dataStr, parseError);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// Chat API
export const chatApi = {
  sendMessage: (request: ChatRequest): Promise<ChatResponse> =>
    fetchApi('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  streamMessage: (request: ChatRequest) =>
    streamApi<ChatResponse>('/api/chat/stream', {
      method: 'POST',
      body: JSON.stringify(request),
    }),
};

// Health API
export const healthApi = {
  check: () => fetchApi<{ status: string }>('/health'),
};

// Export utilities
export { ApiError, type RequestInterceptor, type ResponseInterceptor };

