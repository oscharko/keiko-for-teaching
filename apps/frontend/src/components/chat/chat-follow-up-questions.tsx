'use client';

import { Button } from '@/components/ui/button';
import { MessageCircle } from 'lucide-react';

interface ChatFollowUpQuestionsProps {
	  questions: string[];
	  // Optional click handler so the component can be rendered safely without an action in some contexts
	  onQuestionClick?: (question: string) => void;
	}

	export function ChatFollowUpQuestions({
	  questions,
	  onQuestionClick,
	}: ChatFollowUpQuestionsProps) {
	  // If there are no questions or no click handler, there is nothing actionable to render
	  if (!questions || questions.length === 0 || !onQuestionClick) {
	    return null;
	  }

  return (
    <div className="mt-4 space-y-2">
      <h4 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
        <MessageCircle className="h-4 w-4" />
        Follow-up Questions
      </h4>
      <div className="flex flex-wrap gap-2">
        {questions.map((question, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            onClick={() => onQuestionClick(question)}
            className="text-left h-auto py-2 px-3 whitespace-normal hover:bg-keiko-primary hover:text-keiko-black hover:border-keiko-primary transition-colors"
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  );
}

