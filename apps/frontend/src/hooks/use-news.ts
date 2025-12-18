'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNewsStore, type NewsArticle } from '@/stores/news';

// Mock API functions (replace with actual API calls)
const newsApi = {
  getAll: async (): Promise<NewsArticle[]> => {
    // TODO: Replace with actual API call
    return [];
  },
  
  getById: async (id: string): Promise<NewsArticle> => {
    // TODO: Replace with actual API call
    throw new Error('Not implemented');
  },
  
  markAsRead: async (id: string): Promise<void> => {
    // TODO: Replace with actual API call
  },
  
  toggleFavorite: async (id: string): Promise<void> => {
    // TODO: Replace with actual API call
  },
};

export function useNews() {
  const queryClient = useQueryClient();
  const { setArticles, setLoading, setError, markAsRead, toggleFavorite } = useNewsStore();

  const query = useQuery({
    queryKey: ['news'],
    queryFn: async () => {
      setLoading(true);
      try {
        const articles = await newsApi.getAll();
        setArticles(articles);
        setError(null);
        return articles;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to fetch news';
        setError(errorMessage);
        throw error;
      } finally {
        setLoading(false);
      }
    },
  });

  const markAsReadMutation = useMutation({
    mutationFn: newsApi.markAsRead,
    onSuccess: (_, id) => {
      markAsRead(id);
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });

  const toggleFavoriteMutation = useMutation({
    mutationFn: newsApi.toggleFavorite,
    onSuccess: (_, id) => {
      toggleFavorite(id);
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });

  return {
    articles: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    markAsRead: markAsReadMutation.mutate,
    toggleFavorite: toggleFavoriteMutation.mutate,
  };
}

