'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

export interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

interface UploadProgressProps {
  uploads: UploadProgress[];
}

export function UploadProgressComponent({ uploads }: UploadProgressProps) {
  if (uploads.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        {uploads.map((upload, index) => (
          <div key={index} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {upload.status === 'uploading' && (
                  <Loader2 className="h-4 w-4 animate-spin text-keiko-primary" />
                )}
                {upload.status === 'success' && (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
                {upload.status === 'error' && (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
                <span className="text-sm font-medium">{upload.fileName}</span>
              </div>
              <span className="text-sm text-muted-foreground">
                {upload.progress}%
              </span>
            </div>
            <Progress value={upload.progress} className="h-2" />
            {upload.error && (
              <p className="text-xs text-red-500">{upload.error}</p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

