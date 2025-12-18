/**
 * Tests for useChat hook.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useChat } from '../use-chat'
import { chatApi } from '@/lib/api'
import { useChatStore } from '@/stores/chat'

// Mock the API
vi.mock('@/lib/api', () => ({
  chatApi: {
    sendMessage: vi.fn(),
    streamMessage: vi.fn(),
  },
}))

describe('useChat', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    // Reset store
    useChatStore.getState().clearMessages()
    useChatStore.getState().setError(null)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should initialize with empty messages', () => {
    const { result } = renderHook(() => useChat(), { wrapper })

    expect(result.current.messages).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should send a message in non-streaming mode', async () => {
    const mockResponse = {
      answer: 'Test response',
      citations: [],
      data_points: [],
      follow_up_questions: [],
      thoughts: [],
    }

    vi.mocked(chatApi.sendMessage).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useChat(), { wrapper })

    // Send message
    await result.current.sendMessage('Hello', false)

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2)
    })

    // Check user message
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.messages[0].content).toBe('Hello')

    // Check assistant message
    expect(result.current.messages[1].role).toBe('assistant')
    expect(result.current.messages[1].content).toBe('Test response')
  })

  it('should send a message in streaming mode', async () => {
    const mockChunks = [
      { answer: 'Hello', citations: [], data_points: [], follow_up_questions: [] },
      { answer: ' world', citations: [], data_points: [], follow_up_questions: [] },
      { answer: '!', citations: [], data_points: [], follow_up_questions: ['What else?'] },
    ]

    // Mock async generator
    async function* mockStreamGenerator() {
      for (const chunk of mockChunks) {
        yield chunk
      }
    }

    vi.mocked(chatApi.streamMessage).mockReturnValue(mockStreamGenerator())

    const { result } = renderHook(() => useChat(), { wrapper })

    // Send message with streaming
    await result.current.sendMessage('Hello', true)

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(false)
    })

    // Check messages
    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1].content).toBe('Hello world!')
    expect(result.current.messages[1].followUpQuestions).toEqual(['What else?'])
  })

  it('should handle errors in non-streaming mode', async () => {
    const error = new Error('API Error')
    vi.mocked(chatApi.sendMessage).mockRejectedValue(error)

    const { result } = renderHook(() => useChat(), { wrapper })

    await result.current.sendMessage('Hello', false)

    await waitFor(() => {
      expect(result.current.error).toBe('API Error')
    })
  })

  it('should handle errors in streaming mode', async () => {
    async function* mockStreamGenerator() {
      throw new Error('Streaming Error')
    }

    vi.mocked(chatApi.streamMessage).mockReturnValue(mockStreamGenerator())

    const { result } = renderHook(() => useChat(), { wrapper })

    await result.current.sendMessage('Hello', true)

    await waitFor(() => {
      expect(result.current.error).toBe('Streaming Error')
      expect(result.current.isStreaming).toBe(false)
    })
  })

  it('should clear messages', () => {
    const { result } = renderHook(() => useChat(), { wrapper })

    // Add some messages
    useChatStore.getState().addMessage({
      id: '1',
      role: 'user',
      content: 'Test',
      timestamp: new Date().toISOString(),
    })

    expect(result.current.messages).toHaveLength(1)

    // Clear messages
    result.current.clearMessages()

    expect(result.current.messages).toHaveLength(0)
  })

