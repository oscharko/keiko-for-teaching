'use client';

import { NewsCard } from './news-card';
import type { NewsArticle } from '@/stores/news';

interface NewsListProps {
  articles: NewsArticle[];
  onToggleFavorite?: (id: string) => void;
  onMarkAsRead?: (id: string) => void;
}

export function NewsList({ articles, onToggleFavorite, onMarkAsRead }: NewsListProps) {
  if (articles.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No news articles found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {articles.map((article) => (
        <NewsCard
          key={article.id}
          article={article}
          onToggleFavorite={onToggleFavorite}
          onMarkAsRead={onMarkAsRead}
        />
      ))}
    </div>
  );
}

