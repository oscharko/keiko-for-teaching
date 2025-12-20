'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { IdeaList } from '@/components/ideas/idea-list';
import { IdeaForm } from '@/components/ideas/idea-form';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useIdeas } from '@/hooks/use-ideas';
import { useIdeasStore } from '@/stores/ideas';
import { Plus, Filter } from 'lucide-react';

export default function IdeasPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const { ideas, isLoading, createIdea, upvoteIdea, downvoteIdea } = useIdeas();
  const { filters, setFilters } = useIdeasStore();

  const handleCreateIdea = (ideaData: {
    title: string;
    description: string;
    category: string;
    tags: string[];
  }) => {
    createIdea({
      ...ideaData,
      author: 'Current User', // TODO: Get from auth context
      status: 'draft', // Default status for new ideas
    });
    setDialogOpen(false);
  };

  const filteredIdeas = ideas.filter((idea) => {
    if (filters.category && idea.category !== filters.category) return false;
    if (filters.status && idea.status !== filters.status) return false;
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        idea.title.toLowerCase().includes(searchLower) ||
        idea.description.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-headline font-bold mb-2">Ideas Hub</h1>
          <p className="text-muted-foreground">
            Share and discover innovative ideas from the community
          </p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-keiko-primary text-keiko-black hover:opacity-90">
              <Plus className="mr-2 h-4 w-4" />
              New Idea
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Submit New Idea</DialogTitle>
            </DialogHeader>
            <IdeaForm
              onSubmit={handleCreateIdea}
              onCancel={() => setDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="all" className="mb-6">
        <TabsList>
          <TabsTrigger value="all" onClick={() => setFilters({ status: undefined })}>
            All Ideas
          </TabsTrigger>
          <TabsTrigger value="submitted" onClick={() => setFilters({ status: 'submitted' })}>
            Submitted
          </TabsTrigger>
          <TabsTrigger value="in_review" onClick={() => setFilters({ status: 'in_review' })}>
            In Review
          </TabsTrigger>
          <TabsTrigger value="approved" onClick={() => setFilters({ status: 'approved' })}>
            Approved
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Search and Filters */}
      <div className="mb-6 flex gap-4">
        <input
          type="text"
          placeholder="Search ideas..."
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
          <p className="text-muted-foreground">Loading ideas...</p>
        </div>
      ) : (
        <IdeaList
          ideas={filteredIdeas}
          onUpvote={upvoteIdea}
          onDownvote={downvoteIdea}
        />
      )}
    </div>
  );
}

