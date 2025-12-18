/**
 * Search types for the Keiko search service.
 */

export interface SearchRequest {
  query: string;
  top_k?: number;
  use_semantic_ranker?: boolean;
  query_vector?: number[];
  filter_expression?: string;
}

export interface SearchResult {
  id: string;
  content: string;
  title?: string;
  source?: string;
  score: number;
  reranker_score?: number;
  highlights?: Record<string, string[]>;
}

export interface SearchResponse {
  results: SearchResult[];
  total_count: number;
  query: string;
  cached?: boolean;
}

