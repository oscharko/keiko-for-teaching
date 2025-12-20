import { create } from 'zustand';
import type { Message, ResponseContext } from '@keiko/shared-types';

/**
 * Extended chat message with metadata and context.
 * Includes streaming support and citation tracking.
 */
export interface ChatMessage extends Message {
  /** Unique message identifier */
  id: string;
  /** Message creation timestamp (milliseconds) */
  timestamp: number;
  /** Response context with data points and follow-up questions */
  context?: ResponseContext;
  /** Citation sources from RAG */
  citations?: string[];
  /** Data points from search results */
  dataPoints?: string[];
  /** Follow-up questions suggested by AI */
  followUpQuestions?: string[];
}

/**
 * Chat store state and actions.
 * Manages conversation history, loading states, and error handling.
 */
interface ChatState {
  /** Array of chat messages in conversation order */
  messages: ChatMessage[];
  /** Loading state for API requests */
  isLoading: boolean;
  /** Error message if request failed */
  error: string | null;
  /** Add a new message to the conversation (optimistic update) */
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => string;
  /** Update an existing message (for streaming updates) */
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  /** Set loading state */
  setLoading: (loading: boolean) => void;
  /** Set error message */
  setError: (error: string | null) => void;
  /** Clear all messages and reset state */
  clearMessages: () => void;
}

/**
 * Zustand store for chat state management.
 * Supports optimistic updates for better UX during streaming.
 */
export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,

  /**
   * Add a new message to the conversation.
   * Generates a unique ID and timestamp for optimistic updates.
   * @param message - Message to add (without id and timestamp)
   * @returns Generated message ID
   */
  addMessage: (message) => {
    const id = crypto.randomUUID();
    set((state) => ({
      messages: [
        ...state.messages,
        { ...message, id, timestamp: Date.now() },
      ],
    }));
    return id;
  },

  /**
   * Update an existing message.
   * Used for streaming updates to accumulate content.
   * @param id - Message ID to update
   * @param updates - Partial message updates
   */
  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },

  /** Set the loading state for API requests */
  setLoading: (loading) => set({ isLoading: loading }),

  /** Set error message (null to clear) */
  setError: (error) => set({ error }),

  /** Clear all messages and reset error state */
  clearMessages: () => set({ messages: [], error: null }),
}));

