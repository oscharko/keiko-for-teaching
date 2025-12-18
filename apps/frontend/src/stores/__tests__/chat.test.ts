/**
 * Tests for chat store.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../chat'

describe('useChatStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useChatStore.setState({
      messages: [],
      isLoading: false,
      error: null,
    })
  })

  it('should initialize with empty state', () => {
    const state = useChatStore.getState()

    expect(state.messages).toEqual([])
    expect(state.isLoading).toBe(false)
    expect(state.error).toBeNull()
  })

  it('should add a message', () => {
    const { addMessage } = useChatStore.getState()

    const messageId = addMessage({
      role: 'user',
      content: 'Hello',
    })

    const state = useChatStore.getState()

    expect(state.messages).toHaveLength(1)
    expect(state.messages[0].id).toBe(messageId)
    expect(state.messages[0].role).toBe('user')
    expect(state.messages[0].content).toBe('Hello')
    expect(state.messages[0].timestamp).toBeDefined()
  })

  it('should add multiple messages', () => {
    const { addMessage } = useChatStore.getState()

    addMessage({ role: 'user', content: 'First message' })
    addMessage({ role: 'assistant', content: 'Second message' })
    addMessage({ role: 'user', content: 'Third message' })

    const state = useChatStore.getState()

    expect(state.messages).toHaveLength(3)
    expect(state.messages[0].content).toBe('First message')
    expect(state.messages[1].content).toBe('Second message')
    expect(state.messages[2].content).toBe('Third message')
  })

  it('should update a message', () => {
    const { addMessage, updateMessage } = useChatStore.getState()

    const messageId = addMessage({
      role: 'assistant',
      content: 'Initial content',
    })

    updateMessage(messageId, {
      content: 'Updated content',
      citations: ['citation1', 'citation2'],
    })

    const state = useChatStore.getState()

    expect(state.messages[0].content).toBe('Updated content')
    expect(state.messages[0].citations).toEqual(['citation1', 'citation2'])
  })

  it('should not update non-existent message', () => {
    const { addMessage, updateMessage } = useChatStore.getState()

    addMessage({ role: 'user', content: 'Test' })

    updateMessage('non-existent-id', { content: 'Updated' })

    const state = useChatStore.getState()

    expect(state.messages[0].content).toBe('Test')
  })

  it('should set loading state', () => {
    const { setLoading } = useChatStore.getState()

    setLoading(true)
    expect(useChatStore.getState().isLoading).toBe(true)

    setLoading(false)
    expect(useChatStore.getState().isLoading).toBe(false)
  })

  it('should set error state', () => {
    const { setError } = useChatStore.getState()

    setError('Test error')
    expect(useChatStore.getState().error).toBe('Test error')

    setError(null)
    expect(useChatStore.getState().error).toBeNull()
  })

  it('should clear messages', () => {
    const { addMessage, setError, clearMessages } = useChatStore.getState()

    addMessage({ role: 'user', content: 'Message 1' })
    addMessage({ role: 'assistant', content: 'Message 2' })
    setError('Some error')

    clearMessages()

    const state = useChatStore.getState()

    expect(state.messages).toEqual([])
    expect(state.error).toBeNull()
  })

  it('should preserve message order', () => {
    const { addMessage } = useChatStore.getState()

    const id1 = addMessage({ role: 'user', content: 'First' })
    const id2 = addMessage({ role: 'assistant', content: 'Second' })
    const id3 = addMessage({ role: 'user', content: 'Third' })

    const state = useChatStore.getState()

    expect(state.messages[0].id).toBe(id1)
    expect(state.messages[1].id).toBe(id2)
    expect(state.messages[2].id).toBe(id3)
  })

  it('should handle message with optional fields', () => {
    const { addMessage } = useChatStore.getState()

    addMessage({
      role: 'assistant',
      content: 'Response',
      citations: ['doc1', 'doc2'],
      dataPoints: [{ key: 'value' }],
      followUpQuestions: ['Question 1', 'Question 2'],
    })

    const state = useChatStore.getState()

    expect(state.messages[0].citations).toEqual(['doc1', 'doc2'])
    expect(state.messages[0].dataPoints).toEqual([{ key: 'value' }])
    expect(state.messages[0].followUpQuestions).toEqual(['Question 1', 'Question 2'])
  })
})

