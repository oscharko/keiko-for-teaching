'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Download, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface DocumentFile {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
  url?: string;
  thumbnail?: string;
}

interface FilePreviewProps {
  file: DocumentFile;
  onDownload?: (id: string) => void;
  onView?: (id: string) => void;
}

export function FilePreview({ file, onDownload, onView }: FilePreviewProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getFileIcon = (type: string) => {
    // You can expand this with more specific icons
    return <FileText className="h-12 w-12 text-muted-foreground" />;
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            {file.thumbnail ? (
              <img
                src={file.thumbnail}
                alt={file.name}
                className="w-12 h-12 object-cover rounded"
              />
            ) : (
              getFileIcon(file.type)
            )}
            <div>
              <CardTitle className="text-base">{file.name}</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                {formatFileSize(file.size)}
              </p>
            </div>
          </div>
          <Badge variant="outline">{file.type}</Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Uploaded: {new Date(file.uploadedAt).toLocaleDateString('de-DE')}
          </p>
          <div className="flex gap-2">
            {onView && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onView(file.id)}
              >
                <Eye className="h-4 w-4" />
              </Button>
            )}
            {onDownload && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload(file.id)}
              >
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

