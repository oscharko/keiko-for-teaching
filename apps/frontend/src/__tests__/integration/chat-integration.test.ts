/**
 * Integration tests for Chat API and Hook
 * Tests the complete flow from frontend to backend
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '@/hooks/use-chat';
import { chatApi } from '@/lib/api';

// Mock the API client
jest.mock('@/lib/api', () => ({
  chatApi: {
    sendMessage: jest.fn(),
    streamMessage: jest.fn(),
  },
}));

describe('Chat Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Non-streaming chat', () => {
    it('should send message and receive response', async () => {
      const mockResponse = {
        message: {
          role: 'assistant' as const,
          content: 'Hello! How can I help?',
        },
        context: {
          data_points: {
            text: [],
            images: [],
            citations: [],
          },
          thoughts: [],
          followup_questions: [],
        },
      };

      (chatApi.sendMessage as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('Hello', false);
      });

      expect(result.current.messages).toHaveLength(2); // user + assistant
      expect(result.current.messages[1].content).toBe('Hello! How can I help?');
    });

    it('should handle API errors gracefully', async () => {
      const error = new Error('Network error');
      (chatApi.sendMessage as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('Hello', false);
      });

      expect(result.current.error).toBeTruthy();
    });
  });

  describe('Streaming chat', () => {
    it('should stream message chunks', async () => {
      async function* mockStream() {
        yield {
          message: { role: 'assistant' as const, content: 'Hello' },
          context: {
            data_points: { text: [], images: [], citations: [] },
            thoughts: [],
            followup_questions: [],
          },
        };
        yield {
          message: { role: 'assistant' as const, content: ' world' },
          context: {
            data_points: { text: [], images: [], citations: [] },
            thoughts: [],
            followup_questions: [],
          },
        };
      }

      (chatApi.streamMessage as jest.Mock).mockReturnValue(mockStream());

      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('Hello', true);
      });

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(2);
      });

      expect(result.current.messages[1].content).toBe('Hello world');
    });

    it('should validate empty messages', async () => {
      const { result } = renderHook(() => useChat());

      await act(async () => {
        await result.current.sendMessage('', true);
      });

      expect(result.current.error).toBe('Message cannot be empty');
    });
  });
});

