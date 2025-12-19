'use client';

import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessage } from './chat-message';
import { Loader2 } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '@/stores/chat';

interface ChatMessagesProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  streamingMessageId?: string | null;
  onFollowUpClick?: (question: string) => void;
}

export function ChatMessages({
  messages,
  isLoading,
  streamingMessageId,
  onFollowUpClick,
}: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center">
          <div className="mb-4 flex h-16 w-16 mx-auto items-center justify-center rounded-full bg-keiko-primary">
            <span className="font-headline text-3xl font-bold text-keiko-black">
              K
            </span>
          </div>
          <h2 className="font-headline text-2xl font-bold">
            Willkommen bei Keiko
          </h2>
          <p className="mt-2 text-muted-foreground font-body">
            Stelle eine Frage, um zu beginnen.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1" ref={scrollRef}>
      <div className="space-y-4 p-4">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            isStreaming={streamingMessageId === message.id}
            onFollowUpClick={onFollowUpClick}
          />
        ))}
        {isLoading && !streamingMessageId && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="font-body text-sm">Keiko denkt nach...</span>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}

