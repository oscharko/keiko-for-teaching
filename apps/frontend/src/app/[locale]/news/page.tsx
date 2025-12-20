'use client';

import { NewsList } from '@/components/news/news-list';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { useNews } from '@/hooks/use-news';
import { useNewsStore } from '@/stores/news';
import { Filter, Star, BookOpen } from 'lucide-react';

export default function NewsPage() {
  const { articles, isLoading, markAsRead, toggleFavorite } = useNews();
  const { filters, setFilters } = useNewsStore();

  const filteredArticles = articles.filter((article) => {
    if (filters.category && article.category !== filters.category) return false;
    if (filters.source && article.source !== filters.source) return false;
    if (filters.showOnlyUnread && article.isRead) return false;
    if (filters.showOnlyFavorites && !article.isFavorite) return false;
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        article.title.toLowerCase().includes(searchLower) ||
        article.summary.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  const unreadCount = articles.filter((a) => !a.isRead).length;
  const favoriteCount = articles.filter((a) => a.isFavorite).length;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-headline font-bold mb-2">News Dashboard</h1>
        <p className="text-muted-foreground">
          Stay updated with the latest news and articles
        </p>
      </div>

      <Tabs defaultValue="all" className="mb-6">
        <TabsList>
          <TabsTrigger
            value="all"
            onClick={() => setFilters({ showOnlyUnread: false, showOnlyFavorites: false })}
          >
            All News
          </TabsTrigger>
          <TabsTrigger
            value="unread"
            onClick={() => setFilters({ showOnlyUnread: true, showOnlyFavorites: false })}
          >
            <BookOpen className="mr-2 h-4 w-4" />
            Unread ({unreadCount})
          </TabsTrigger>
          <TabsTrigger
            value="favorites"
            onClick={() => setFilters({ showOnlyUnread: false, showOnlyFavorites: true })}
          >
            <Star className="mr-2 h-4 w-4" />
            Favorites ({favoriteCount})
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Search and Filters */}
      <div className="mb-6 flex gap-4">
        <input
          type="text"
          placeholder="Search news..."
          value={filters.search || ''}
          onChange={(e) => setFilters({ search: e.target.value })}
          className="flex-1 px-4 py-2 border rounded-md"
        />
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          Filters
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading news...</p>
        </div>
      ) : (
        <NewsList
          articles={filteredArticles}
          onMarkAsRead={markAsRead}
          onToggleFavorite={toggleFavorite}
        />
      )}
    </div>
  );
}

