'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  error?: string;
}

export function ChatInput({ onSend, disabled, error }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = useCallback(() => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  }, [input, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Stelle eine Frage..."
          disabled={disabled}
          className="min-h-[60px] resize-none font-body"
        />
        <Button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          size="icon"
          className="h-[60px] w-[60px]"
          aria-label="Nachricht senden"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
      {error && <p className="text-sm text-destructive font-body">{error}</p>}
    </div>
  );
}

