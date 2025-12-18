'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useIdeasStore, type Idea } from '@/stores/ideas';

// Mock API functions (replace with actual API calls)
const ideasApi = {
  getAll: async (): Promise<Idea[]> => {
    // TODO: Replace with actual API call
    return [];
  },
  
  getById: async (id: string): Promise<Idea> => {
    // TODO: Replace with actual API call
    throw new Error('Not implemented');
  },
  
  create: async (idea: Omit<Idea, 'id' | 'createdAt' | 'updatedAt' | 'upvotes' | 'downvotes' | 'comments'>): Promise<Idea> => {
    // TODO: Replace with actual API call
    const newIdea: Idea = {
      ...idea,
      id: Math.random().toString(36).substr(2, 9),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      upvotes: 0,
      downvotes: 0,
      comments: 0,
      status: 'draft',
    };
    return newIdea;
  },
  
  update: async (id: string, updates: Partial<Idea>): Promise<Idea> => {
    // TODO: Replace with actual API call
    throw new Error('Not implemented');
  },
  
  delete: async (id: string): Promise<void> => {
    // TODO: Replace with actual API call
  },
  
  upvote: async (id: string): Promise<void> => {
    // TODO: Replace with actual API call
  },
  
  downvote: async (id: string): Promise<void> => {
    // TODO: Replace with actual API call
  },
  
  getSimilar: async (id: string): Promise<Idea[]> => {
    // TODO: Replace with actual API call
    return [];
  },
};

export function useIdeas() {
  const queryClient = useQueryClient();
  const { setIdeas, setLoading, setError } = useIdeasStore();

  const query = useQuery({
    queryKey: ['ideas'],
    queryFn: async () => {
      setLoading(true);
      try {
        const ideas = await ideasApi.getAll();
        setIdeas(ideas);
        setError(null);
        return ideas;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to fetch ideas';
        setError(errorMessage);
        throw error;
      } finally {
        setLoading(false);
      }
    },
  });

  const createMutation = useMutation({
    mutationFn: ideasApi.create,
    onSuccess: (newIdea) => {
      queryClient.invalidateQueries({ queryKey: ['ideas'] });
      useIdeasStore.getState().addIdea(newIdea);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Idea> }) =>
      ideasApi.update(id, updates),
    onSuccess: (updatedIdea) => {
      queryClient.invalidateQueries({ queryKey: ['ideas'] });
      useIdeasStore.getState().updateIdea(updatedIdea.id, updatedIdea);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ideasApi.delete,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['ideas'] });
      useIdeasStore.getState().deleteIdea(id);
    },
  });

  const upvoteMutation = useMutation({
    mutationFn: ideasApi.upvote,
    onSuccess: (_, id) => {
      useIdeasStore.getState().upvoteIdea(id);
      queryClient.invalidateQueries({ queryKey: ['ideas'] });
    },
  });

  const downvoteMutation = useMutation({
    mutationFn: ideasApi.downvote,
    onSuccess: (_, id) => {
      useIdeasStore.getState().downvoteIdea(id);
      queryClient.invalidateQueries({ queryKey: ['ideas'] });
    },
  });

  return {
    ideas: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    createIdea: createMutation.mutate,
    updateIdea: (id: string, updates: Partial<Idea>) =>
      updateMutation.mutate({ id, updates }),
    deleteIdea: deleteMutation.mutate,
    upvoteIdea: upvoteMutation.mutate,
    downvoteIdea: downvoteMutation.mutate,
  };
}

export function useIdea(id: string) {
  const { setCurrentIdea, setLoading, setError } = useIdeasStore();

  return useQuery({
    queryKey: ['idea', id],
    queryFn: async () => {
      setLoading(true);
      try {
        const idea = await ideasApi.getById(id);
        setCurrentIdea(idea);
        setError(null);
        return idea;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to fetch idea';
        setError(errorMessage);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    enabled: !!id,
  });
}

export function useSimilarIdeas(id: string) {
  return useQuery({
    queryKey: ['similar-ideas', id],
    queryFn: () => ideasApi.getSimilar(id),
    enabled: !!id,
  });
}

