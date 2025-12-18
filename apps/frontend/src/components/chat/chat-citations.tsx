'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, FileText } from 'lucide-react';

export interface Citation {
  id: string;
  title: string;
  content: string;
  source?: string;
  url?: string;
  score?: number;
}

interface ChatCitationsProps {
  citations: Citation[];
}

export function ChatCitations({ citations }: ChatCitationsProps) {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-2">
      <h4 className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
        <FileText className="h-4 w-4" />
        Sources ({citations.length})
      </h4>
      <div className="grid gap-2">
        {citations.map((citation, index) => (
          <Card key={citation.id} className="border-l-4 border-l-keiko-primary">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono">
                    [{index + 1}]
                  </Badge>
                  {citation.title}
                </span>
                {citation.url && (
                  <a
                    href={citation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-keiko-primary hover:opacity-80"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="pb-3">
              <p className="text-sm text-muted-foreground line-clamp-2">
                {citation.content}
              </p>
              {citation.source && (
                <p className="text-xs text-muted-foreground mt-2">
                  Source: {citation.source}
                </p>
              )}
              {citation.score !== undefined && (
                <p className="text-xs text-muted-foreground mt-1">
                  Relevance: {(citation.score * 100).toFixed(1)}%
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

