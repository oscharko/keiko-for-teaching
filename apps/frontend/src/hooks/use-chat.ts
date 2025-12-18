'use client';

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useChatStore } from '@/stores/chat';
import { chatApi } from '@/lib/api';
import type { ChatRequest, ChatResponse } from '@keiko/shared-types';

export function useChat() {
  const { messages, addMessage, updateMessage, clearMessages, setLoading, setError } = useChatStore();
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessageMutation = useMutation({
    mutationFn: (request: ChatRequest) => chatApi.sendMessage(request),
    onSuccess: (response) => {
      addMessage({
        id: Date.now().toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        citations: response.citations,
        dataPoints: response.data_points,
        followUpQuestions: response.follow_up_questions,
      });
      setError(null);
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      setError(errorMessage);
    },
  });

  const sendMessage = useCallback(
    async (content: string, useStreaming = true) => {
      // Add user message
      const userMessage = {
        id: Date.now().toString(),
        role: 'user' as const,
        content,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMessage);

      const request: ChatRequest = {
        message: content,
        conversation_id: 'default', // TODO: Implement conversation management
        use_rag: true,
      };

      if (useStreaming) {
        setIsStreaming(true);
        setLoading(true);

        try {
          const assistantMessageId = (Date.now() + 1).toString();
          let accumulatedContent = '';
          let citations: any[] = [];
          let dataPoints: any[] = [];
          let followUpQuestions: string[] = [];

          // Add placeholder assistant message
          addMessage({
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
          });

          // Stream the response
          for await (const chunk of chatApi.streamMessage(request)) {
            if (chunk.answer) {
              accumulatedContent += chunk.answer;
            }
            if (chunk.citations) {
              citations = chunk.citations;
            }
            if (chunk.data_points) {
              dataPoints = chunk.data_points;
            }
            if (chunk.follow_up_questions) {
              followUpQuestions = chunk.follow_up_questions;
            }

            // Update the message with accumulated content
            updateMessage(assistantMessageId, {
              content: accumulatedContent,
              citations,
              dataPoints,
              followUpQuestions,
            });
          }

          setError(null);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Streaming failed';
          setError(errorMessage);
        } finally {
          setIsStreaming(false);
          setLoading(false);
        }
      } else {
        // Non-streaming mode
        sendMessageMutation.mutate(request);
      }
    },
    [addMessage, updateMessage, setLoading, setError, sendMessageMutation]
  );

  const retry = useCallback(() => {
    const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMessage) {
      sendMessage(lastUserMessage.content);
    }
  }, [messages, sendMessage]);

  return {
    messages,
    sendMessage,
    clearMessages,
    retry,
    isLoading: sendMessageMutation.isPending || isStreaming,
    isStreaming,
    error: useChatStore.getState().error,
  };
}

