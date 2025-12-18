/**
 * News types for the Keiko news service.
 */

export type NewsCategory = 
  | 'technology'
  | 'business'
  | 'science'
  | 'health'
  | 'general';

export type NewsSentiment = 'positive' | 'neutral' | 'negative';

export interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content?: string;
  source: string;
  author?: string;
  published_at: string;
  url: string;
  image_url?: string;
  category: NewsCategory;
  sentiment?: NewsSentiment;
  tags?: string[];
  relevance_score?: number;
}

export interface NewsListResponse {
  articles: NewsArticle[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface NewsRequest {
  category?: NewsCategory;
  query?: string;
  page?: number;
  page_size?: number;
  from_date?: string;
  to_date?: string;
}

