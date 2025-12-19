'use client';

import { cn } from '@/lib/utils';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { User, Bot, Loader2 } from 'lucide-react';
import { ChatCitations } from './chat-citations';
import { ChatDataPoints } from './chat-data-points';
import { ChatFollowUpQuestions } from './chat-follow-up-questions';
import type { ChatMessage as ChatMessageModel } from '@/stores/chat';

interface ChatMessageProps {
	  // Full chat message model as stored in the chat store
	  message: ChatMessageModel;
	  isStreaming?: boolean;
	  onFollowUpClick?: (question: string) => void;
	}

export function ChatMessage({ message, isStreaming, onFollowUpClick }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn('flex gap-3 p-4', isUser ? 'flex-row-reverse' : 'flex-row')}
      data-role={message.role}
    >
      <Avatar
        className={cn('h-8 w-8', isUser ? 'bg-keiko-primary' : 'bg-keiko-black')}
      >
        <AvatarFallback
          className={cn(
            isUser
              ? 'bg-keiko-primary text-keiko-black'
              : 'bg-keiko-black text-keiko-white'
          )}
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          'max-w-[80%] rounded-lg px-4 py-2 font-body',
          isUser
            ? 'bg-keiko-primary text-keiko-black'
            : 'bg-muted text-foreground'
        )}
      >
        <div className="flex items-start gap-2">
          <p className="whitespace-pre-wrap flex-1">{message.content}</p>
          {isStreaming && !isUser && (
            <Loader2 className="h-4 w-4 animate-spin text-keiko-primary" />
          )}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-3">
            <ChatCitations citations={message.citations} />
          </div>
        )}

        {/* Data Points */}
        {message.dataPoints && message.dataPoints.length > 0 && (
          <div className="mt-3">
            <ChatDataPoints dataPoints={message.dataPoints} />
          </div>
        )}

        {/* Follow-up Questions */}
        {(message.followUpQuestions || message.context?.followup_questions) && (
          <div className="mt-3">
            <ChatFollowUpQuestions
              questions={message.followUpQuestions || message.context?.followup_questions || []}
              onQuestionClick={onFollowUpClick}
            />
          </div>
        )}
      </div>
    </div>
  );
}

