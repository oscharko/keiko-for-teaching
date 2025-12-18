import { create } from 'zustand';

export interface Idea {
  id: string;
  title: string;
  description: string;
  category: string;
  tags: string[];
  status: 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected';
  author: string;
  createdAt: string;
  updatedAt: string;
  upvotes: number;
  downvotes: number;
  comments: number;
  similarIdeas?: string[];
}

interface IdeasState {
  ideas: Idea[];
  currentIdea: Idea | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    category?: string;
    status?: string;
    search?: string;
  };
  
  // Actions
  setIdeas: (ideas: Idea[]) => void;
  addIdea: (idea: Idea) => void;
  updateIdea: (id: string, updates: Partial<Idea>) => void;
  deleteIdea: (id: string) => void;
  setCurrentIdea: (idea: Idea | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<IdeasState['filters']>) => void;
  clearFilters: () => void;
  upvoteIdea: (id: string) => void;
  downvoteIdea: (id: string) => void;
}

export const useIdeasStore = create<IdeasState>((set) => ({
  ideas: [],
  currentIdea: null,
  isLoading: false,
  error: null,
  filters: {},

  setIdeas: (ideas) => set({ ideas }),
  
  addIdea: (idea) => set((state) => ({ 
    ideas: [idea, ...state.ideas] 
  })),
  
  updateIdea: (id, updates) => set((state) => ({
    ideas: state.ideas.map((idea) =>
      idea.id === id ? { ...idea, ...updates } : idea
    ),
    currentIdea: state.currentIdea?.id === id 
      ? { ...state.currentIdea, ...updates } 
      : state.currentIdea,
  })),
  
  deleteIdea: (id) => set((state) => ({
    ideas: state.ideas.filter((idea) => idea.id !== id),
    currentIdea: state.currentIdea?.id === id ? null : state.currentIdea,
  })),
  
  setCurrentIdea: (idea) => set({ currentIdea: idea }),
  
  setLoading: (isLoading) => set({ isLoading }),
  
  setError: (error) => set({ error }),
  
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters },
  })),
  
  clearFilters: () => set({ filters: {} }),
  
  upvoteIdea: (id) => set((state) => ({
    ideas: state.ideas.map((idea) =>
      idea.id === id ? { ...idea, upvotes: idea.upvotes + 1 } : idea
    ),
  })),
  
  downvoteIdea: (id) => set((state) => ({
    ideas: state.ideas.map((idea) =>
      idea.id === id ? { ...idea, downvotes: idea.downvotes + 1 } : idea
    ),
  })),
}));

