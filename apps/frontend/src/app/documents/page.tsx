'use client';

import { UploadComponent } from '@/components/documents/upload-component';
import { DocumentList } from '@/components/documents/document-list';
import { UploadProgressComponent } from '@/components/documents/upload-progress';
import { useDocuments } from '@/hooks/use-documents';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, FileText } from 'lucide-react';

export default function DocumentsPage() {
  const {
    documents,
    isLoading,
    uploadDocuments,
    downloadDocument,
    uploadProgress,
    isUploading,
  } = useDocuments();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-headline font-bold mb-2">Documents</h1>
        <p className="text-muted-foreground">
          Upload and manage your documents for AI-powered analysis
        </p>
      </div>

      <Tabs defaultValue="upload" className="mb-6">
        <TabsList>
          <TabsTrigger value="upload">
            <Upload className="mr-2 h-4 w-4" />
            Upload
          </TabsTrigger>
          <TabsTrigger value="library">
            <FileText className="mr-2 h-4 w-4" />
            Library ({documents.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-6">
          <UploadComponent onUpload={uploadDocuments} />
          {uploadProgress.length > 0 && (
            <UploadProgressComponent uploads={uploadProgress} />
          )}
        </TabsContent>

        <TabsContent value="library">
          {isLoading ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading documents...</p>
            </div>
          ) : (
            <DocumentList
              documents={documents}
              onDownload={downloadDocument}
              onView={(id) => console.log('View document:', id)}
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

