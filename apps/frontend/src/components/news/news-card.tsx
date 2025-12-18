'use client';

import Link from 'next/link';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, Star, BookOpen, Calendar } from 'lucide-react';
import type { NewsArticle } from '@/stores/news';

interface NewsCardProps {
  article: NewsArticle;
  onToggleFavorite?: (id: string) => void;
  onMarkAsRead?: (id: string) => void;
}

export function NewsCard({ article, onToggleFavorite, onMarkAsRead }: NewsCardProps) {
  return (
    <Card className={`hover:shadow-lg transition-shadow ${!article.isRead ? 'border-l-4 border-l-keiko-primary' : ''}`}>
      {article.imageUrl && (
        <div className="w-full h-48 overflow-hidden rounded-t-lg">
          <img
            src={article.imageUrl}
            alt={article.title}
            className="w-full h-full object-cover hover:scale-105 transition-transform"
          />
        </div>
      )}
      
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-keiko-primary transition-colors"
              onClick={() => onMarkAsRead?.(article.id)}
            >
              {article.title}
            </a>
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onToggleFavorite?.(article.id)}
            className={article.isFavorite ? 'text-yellow-500' : ''}
          >
            <Star className={`h-4 w-4 ${article.isFavorite ? 'fill-current' : ''}`} />
          </Button>
        </div>
        
        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-2">
          <span>{article.source}</span>
          {article.author && (
            <>
              <span>•</span>
              <span>{article.author}</span>
            </>
          )}
          <span>•</span>
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>{new Date(article.publishedAt).toLocaleDateString('de-DE')}</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-3">
          {article.summary}
        </p>
        
        <div className="flex flex-wrap gap-2 mt-4">
          <Badge variant="outline">{article.category}</Badge>
          {article.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="secondary">
              {tag}
            </Badge>
          ))}
          {article.tags.length > 3 && (
            <Badge variant="secondary">+{article.tags.length - 3}</Badge>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {!article.isRead && (
            <Badge variant="default" className="bg-keiko-primary text-keiko-black">
              New
            </Badge>
          )}
        </div>
        
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => onMarkAsRead?.(article.id)}
        >
          <Button variant="outline" size="sm" className="gap-2">
            Read More
            <ExternalLink className="h-3 w-3" />
          </Button>
        </a>
      </CardFooter>
    </Card>
  );
}

