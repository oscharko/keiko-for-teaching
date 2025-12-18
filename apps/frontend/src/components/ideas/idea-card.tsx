'use client';

import Link from 'next/link';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ThumbsUp, ThumbsDown, MessageCircle, User } from 'lucide-react';
import type { Idea } from '@/stores/ideas';

interface IdeaCardProps {
  idea: Idea;
  onUpvote?: (id: string) => void;
  onDownvote?: (id: string) => void;
}

export function IdeaCard({ idea, onUpvote, onDownvote }: IdeaCardProps) {
  const statusColors = {
    draft: 'bg-gray-500',
    submitted: 'bg-blue-500',
    in_review: 'bg-yellow-500',
    approved: 'bg-green-500',
    rejected: 'bg-red-500',
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <Link href={`/ideas/${idea.id}`} className="flex-1">
            <CardTitle className="hover:text-keiko-primary transition-colors">
              {idea.title}
            </CardTitle>
          </Link>
          <Badge className={statusColors[idea.status]}>
            {idea.status.replace('_', ' ')}
          </Badge>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-2">
          <User className="h-4 w-4" />
          <span>{idea.author}</span>
          <span>•</span>
          <span>{new Date(idea.createdAt).toLocaleDateString('de-DE')}</span>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-3">
          {idea.description}
        </p>
        
        <div className="flex flex-wrap gap-2 mt-4">
          <Badge variant="outline">{idea.category}</Badge>
          {idea.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="secondary">
              {tag}
            </Badge>
          ))}
          {idea.tags.length > 3 && (
            <Badge variant="secondary">+{idea.tags.length - 3}</Badge>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onUpvote?.(idea.id)}
            className="gap-1"
          >
            <ThumbsUp className="h-4 w-4" />
            <span>{idea.upvotes}</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDownvote?.(idea.id)}
            className="gap-1"
          >
            <ThumbsDown className="h-4 w-4" />
            <span>{idea.downvotes}</span>
          </Button>
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <MessageCircle className="h-4 w-4" />
            <span>{idea.comments}</span>
          </div>
        </div>
        
        <Link href={`/ideas/${idea.id}`}>
          <Button variant="outline" size="sm">
            View Details
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}

