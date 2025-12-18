import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatOverrides } from '@keiko/shared-types';

interface SettingsState {
  theme: 'light' | 'dark' | 'system';
  chatOverrides: ChatOverrides;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setChatOverrides: (overrides: Partial<ChatOverrides>) => void;
  resetChatOverrides: () => void;
}

const defaultOverrides: ChatOverrides = {
  retrieval_mode: 'hybrid',
  semantic_ranker: true,
  semantic_captions: false,
  top: 5,
  temperature: 0.7,
  suggest_followup_questions: true,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'system',
      chatOverrides: defaultOverrides,

      setTheme: (theme) => set({ theme }),

      setChatOverrides: (overrides) =>
        set((state) => ({
          chatOverrides: { ...state.chatOverrides, ...overrides },
        })),

      resetChatOverrides: () => set({ chatOverrides: defaultOverrides }),
    }),
    {
      name: 'keiko-settings',
    }
  )
);

