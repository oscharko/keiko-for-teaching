'use client';

import { useCallback } from 'react';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { useChatStore } from '@/stores/chat';
import { useSettingsStore } from '@/stores/settings';
import { chatApi } from '@/lib/api';

export function ChatContainer() {
  const { messages, isLoading, error, addMessage, updateMessage, setLoading, setError } =
    useChatStore();
  const { chatOverrides } = useSettingsStore();

  const handleSendMessage = useCallback(
    async (content: string) => {
      const userMessageId = addMessage({ role: 'user', content });
      setLoading(true);
      setError(null);

      const assistantMessageId = addMessage({
        role: 'assistant',
        content: '',
      });

      try {
        const chatMessages = messages
          .filter((m) => m.role !== 'system')
          .map((m) => ({ role: m.role, content: m.content }));
        chatMessages.push({ role: 'user', content });

        const response = await chatApi.sendMessage({
          messages: chatMessages,
          context: { overrides: chatOverrides },
        });

        updateMessage(assistantMessageId, {
          content: response.message.content,
          context: response.context,
        });
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
        updateMessage(assistantMessageId, {
          content: 'Sorry, an error occurred. Please try again.',
        });
      } finally {
        setLoading(false);
      }
    },
    [messages, chatOverrides, addMessage, updateMessage, setLoading, setError]
  );

  return (
    <div className="flex h-full flex-col">
      <ChatMessages messages={messages} isLoading={isLoading} />
      <div className="border-t border-border p-4">
        <ChatInput
          onSend={handleSendMessage}
          disabled={isLoading}
          error={error ?? undefined}
        />
      </div>
    </div>
  );
}

