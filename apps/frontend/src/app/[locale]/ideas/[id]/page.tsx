'use client';

import { use } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SimilarIdeas } from '@/components/ideas/similar-ideas';
import { useIdea, useSimilarIdeas } from '@/hooks/use-ideas';
import { ThumbsUp, ThumbsDown, MessageCircle, User, Calendar, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function IdeaDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: idea, isLoading } = useIdea(id);
  const { data: similarIdeas } = useSimilarIdeas(id);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Loading idea...</p>
      </div>
    );
  }

  if (!idea) {
    return (
      <div className="container mx-auto px-4 py-8">
        <p className="text-center text-muted-foreground">Idea not found</p>
      </div>
    );
  }

  const statusColors = {
    draft: 'bg-gray-500',
    submitted: 'bg-blue-500',
    in_review: 'bg-yellow-500',
    approved: 'bg-green-500',
    rejected: 'bg-red-500',
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <Link href="/ideas">
        <Button variant="ghost" className="mb-6">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Ideas
        </Button>
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <CardTitle className="text-3xl font-headline">{idea.title}</CardTitle>
                <Badge className={statusColors[idea.status]}>
                  {idea.status.replace('_', ' ')}
                </Badge>
              </div>
              
              <div className="flex items-center gap-4 text-sm text-muted-foreground mt-4">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span>{idea.author}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>{new Date(idea.createdAt).toLocaleDateString('de-DE')}</span>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Description</h3>
                <p className="text-muted-foreground whitespace-pre-wrap">{idea.description}</p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Category</h3>
                <Badge variant="outline">{idea.category}</Badge>
              </div>

              {idea.tags.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {idea.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center gap-4 pt-4 border-t">
                <Button variant="outline" className="gap-2">
                  <ThumbsUp className="h-4 w-4" />
                  Upvote ({idea.upvotes})
                </Button>
                <Button variant="outline" className="gap-2">
                  <ThumbsDown className="h-4 w-4" />
                  Downvote ({idea.downvotes})
                </Button>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <MessageCircle className="h-4 w-4" />
                  <span>{idea.comments} comments</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Comments section placeholder */}
          <Card>
            <CardHeader>
              <CardTitle>Comments</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground text-center py-8">
                Comments feature coming soon
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {similarIdeas && similarIdeas.length > 0 && (
            <SimilarIdeas ideas={similarIdeas} />
          )}
        </div>
      </div>
    </div>
  );
}

