'use client';

import { FilePreview, type DocumentFile } from './file-preview';

interface DocumentListProps {
  documents: DocumentFile[];
  onDownload?: (id: string) => void;
  onView?: (id: string) => void;
}

export function DocumentList({ documents, onDownload, onView }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {documents.map((doc) => (
        <FilePreview
          key={doc.id}
          file={doc}
          onDownload={onDownload}
          onView={onView}
        />
      ))}
    </div>
  );
}

