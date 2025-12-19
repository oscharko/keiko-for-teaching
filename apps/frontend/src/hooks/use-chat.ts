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
        role: 'assistant',
        content: response.message.content,
        citations: response.context?.data_points?.citations,
        dataPoints: response.context?.data_points?.text,
        followUpQuestions: response.context?.followup_questions,
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
      addMessage({
        role: 'user',
        content,
      });

      // Build messages array from conversation history
      const conversationMessages = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      // Add the new user message
      conversationMessages.push({
        role: 'user' as const,
        content,
      });

      const request: ChatRequest = {
        messages: conversationMessages,
        context: {
          overrides: {
            use_rag: true,
            suggest_followup_questions: true,
          },
        },
      };

      if (useStreaming) {
        setIsStreaming(true);
        setLoading(true);

        try {
          let accumulatedContent = '';
          let citations: any[] = [];
          let dataPoints: any[] = [];
          let followUpQuestions: string[] = [];

          // Add placeholder assistant message and get its ID
          const assistantMessageId = addMessage({
            role: 'assistant',
            content: '',
          });

          // Stream the response
          for await (const chunk of chatApi.streamMessage(request)) {
            if (chunk.message?.content) {
              accumulatedContent += chunk.message.content;
            }
            if (chunk.context?.data_points?.citations) {
              citations = chunk.context.data_points.citations;
            }
            if (chunk.context?.data_points?.text) {
              dataPoints = chunk.context.data_points.text;
            }
            if (chunk.context?.followup_questions) {
              followUpQuestions = chunk.context.followup_questions;
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

