'use client';

import { IdeaCard } from './idea-card';
import type { Idea } from '@/stores/ideas';

interface IdeaListProps {
  ideas: Idea[];
  onUpvote?: (id: string) => void;
  onDownvote?: (id: string) => void;
}

export function IdeaList({ ideas, onUpvote, onDownvote }: IdeaListProps) {
  if (ideas.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No ideas found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {ideas.map((idea) => (
        <IdeaCard
          key={idea.id}
          idea={idea}
          onUpvote={onUpvote}
          onDownvote={onDownvote}
        />
      ))}
    </div>
  );
}

