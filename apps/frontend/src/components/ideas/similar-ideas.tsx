'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Lightbulb } from 'lucide-react';
import type { Idea } from '@/stores/ideas';

interface SimilarIdeasProps {
  ideas: Idea[];
}

export function SimilarIdeas({ ideas }: SimilarIdeasProps) {
  if (!ideas || ideas.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          Similar Ideas
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {ideas.map((idea) => (
          <Link
            key={idea.id}
            href={`/ideas/${idea.id}`}
            className="block p-3 rounded-lg border hover:bg-muted transition-colors"
          >
            <h4 className="font-semibold text-sm mb-1 hover:text-keiko-primary">
              {idea.title}
            </h4>
            <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
              {idea.description}
            </p>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {idea.category}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {idea.upvotes} upvotes
              </span>
            </div>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}

