import { create } from 'zustand';

export interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  source: string;
  author?: string;
  publishedAt: string;
  url: string;
  imageUrl?: string;
  category: string;
  tags: string[];
  isRead: boolean;
  isFavorite: boolean;
}

interface NewsState {
  articles: NewsArticle[];
  isLoading: boolean;
  error: string | null;
  filters: {
    category?: string;
    source?: string;
    search?: string;
    showOnlyUnread?: boolean;
    showOnlyFavorites?: boolean;
  };
  
  // Actions
  setArticles: (articles: NewsArticle[]) => void;
  addArticle: (article: NewsArticle) => void;
  updateArticle: (id: string, updates: Partial<NewsArticle>) => void;
  markAsRead: (id: string) => void;
  markAsUnread: (id: string) => void;
  toggleFavorite: (id: string) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<NewsState['filters']>) => void;
  clearFilters: () => void;
}

export const useNewsStore = create<NewsState>((set) => ({
  articles: [],
  isLoading: false,
  error: null,
  filters: {},

  setArticles: (articles) => set({ articles }),
  
  addArticle: (article) => set((state) => ({ 
    articles: [article, ...state.articles] 
  })),
  
  updateArticle: (id, updates) => set((state) => ({
    articles: state.articles.map((article) =>
      article.id === id ? { ...article, ...updates } : article
    ),
  })),
  
  markAsRead: (id) => set((state) => ({
    articles: state.articles.map((article) =>
      article.id === id ? { ...article, isRead: true } : article
    ),
  })),
  
  markAsUnread: (id) => set((state) => ({
    articles: state.articles.map((article) =>
      article.id === id ? { ...article, isRead: false } : article
    ),
  })),
  
  toggleFavorite: (id) => set((state) => ({
    articles: state.articles.map((article) =>
      article.id === id ? { ...article, isFavorite: !article.isFavorite } : article
    ),
  })),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
  })),
  
  clearFilters: () => set({ filters: {} }),
}));

