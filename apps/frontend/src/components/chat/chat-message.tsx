'use client';

import { cn } from '@/lib/utils';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { User, Bot } from 'lucide-react';

interface ChatMessageProps {
  message: {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    context?: {
      followup_questions?: string[];
    };
  };
}

export function ChatMessage({ message }: ChatMessageProps) {
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
        <p className="whitespace-pre-wrap">{message.content}</p>

        {message.context?.followup_questions &&
          message.context.followup_questions.length > 0 && (
            <div className="mt-3 border-t border-border/50 pt-3">
              <p className="text-xs font-headline uppercase tracking-wide mb-2">
                Folgefragen
              </p>
              <ul className="space-y-1">
                {message.context.followup_questions.map((q, i) => (
                  <li
                    key={i}
                    className="text-sm hover:underline cursor-pointer"
                  >
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}
      </div>
    </div>
  );
}

