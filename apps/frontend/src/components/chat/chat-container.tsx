'use client';

import { useCallback, useState } from 'react';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { useChatStore } from '@/stores/chat';
import { useSettingsStore } from '@/stores/settings';
import { useChat } from '@/hooks/use-chat';

export function ChatContainer() {
  const { messages, clearMessages } = useChatStore();
  const { chatOverrides } = useSettingsStore();
  const { sendMessage, isLoading, isStreaming, error } = useChat();
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);

  const handleSendMessage = useCallback(
    async (content: string) => {
      // Use streaming by default
      await sendMessage(content, true);
    },
    [sendMessage]
  );

  const handleClearChat = useCallback(() => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      clearMessages();
    }
  }, [clearMessages]);

  const handleFollowUpClick = useCallback(
    (question: string) => {
      sendMessage(question, true);
    },
    [sendMessage]
  );

  return (
    <div className="flex h-full flex-col">
      <ChatMessages
        messages={messages}
        isLoading={isLoading}
        streamingMessageId={isStreaming ? messages[messages.length - 1]?.id : null}
        onFollowUpClick={handleFollowUpClick}
      />
      <div className="border-t border-border p-4">
        <ChatInput
          onSend={handleSendMessage}
          onClear={handleClearChat}
          disabled={isLoading}
          error={error ?? undefined}
        />
      </div>
    </div>
  );
}

