import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'student' | 'teacher' | 'admin';
  department?: string;
  bio?: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'de';
  notifications: {
    email: boolean;
    push: boolean;
    ideas: boolean;
    news: boolean;
    chat: boolean;
  };
  chatSettings: {
    streamResponses: boolean;
    showCitations: boolean;
    showFollowUpQuestions: boolean;
  };
}

interface UserState {
  profile: UserProfile | null;
  preferences: UserPreferences;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setProfile: (profile: UserProfile | null) => void;
  updateProfile: (updates: Partial<UserProfile>) => void;
  setPreferences: (preferences: Partial<UserPreferences>) => void;
  updatePreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => void;
  setAuthenticated: (isAuthenticated: boolean) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  logout: () => void;
}

const defaultPreferences: UserPreferences = {
  theme: 'system',
  language: 'de',
  notifications: {
    email: true,
    push: true,
    ideas: true,
    news: true,
    chat: true,
  },
  chatSettings: {
    streamResponses: true,
    showCitations: true,
    showFollowUpQuestions: true,
  },
};

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      profile: null,
      preferences: defaultPreferences,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setProfile: (profile) => set({ 
        profile,
        isAuthenticated: !!profile,
      }),
      
      updateProfile: (updates) => set((state) => ({
        profile: state.profile ? { ...state.profile, ...updates } : null,
      })),
      
      setPreferences: (preferences) => set((state) => ({
        preferences: { ...state.preferences, ...preferences },
      })),
      
      updatePreference: (key, value) => set((state) => ({
        preferences: { ...state.preferences, [key]: value },
      })),
      
      setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
      
      setLoading: (isLoading) => set({ isLoading }),
      
      setError: (error) => set({ error }),
      
      logout: () => set({
        profile: null,
        isAuthenticated: false,
        preferences: defaultPreferences,
      }),
    }),
    {
      name: 'keiko-user-storage',
      partialize: (state) => ({
        profile: state.profile,
        preferences: state.preferences,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

