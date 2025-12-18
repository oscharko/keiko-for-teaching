use std::io::Cursor;
use tonic::{Request, Response, Status};

use crate::parser::{LocalPdfParser, Parser};
use crate::splitter::{SentenceTextSplitter, TextSplitter};

pub mod proto {
    tonic::include_proto!("keiko.ingestion.v1");
}

use proto::ingestion_service_server::{IngestionService, IngestionServiceServer};
use proto::{
    Chunk as ProtoChunk, DocumentMetadata, GetSupportedFormatsRequest,
    GetSupportedFormatsResponse, HealthCheckRequest, HealthCheckResponse,
    ParseDocumentRequest, ParseDocumentResponse, ProcessingStats,
};

#[derive(Default)]
pub struct IngestionServiceImpl;

#[tonic::async_trait]
impl IngestionService for IngestionServiceImpl {
    async fn parse_document(
        &self,
        request: Request<ParseDocumentRequest>,
    ) -> Result<Response<ParseDocumentResponse>, Status> {
        let start = std::time::Instant::now();
        let req = request.into_inner();

        let parser = LocalPdfParser::new();
        let pages = parser
            .parse(Cursor::new(&req.content))
            .map_err(|e| Status::invalid_argument(e.to_string()))?;

        let options = req.options.unwrap_or_default();
        let max_tokens = if options.max_tokens_per_chunk > 0 {
            options.max_tokens_per_chunk as usize
        } else {
            500
        };
        let overlap = if options.overlap_percent > 0 {
            options.overlap_percent as usize
        } else {
            10
        };

        let splitter = SentenceTextSplitter::new(max_tokens, overlap);
        let chunks = splitter.split(&pages);

        let total_tokens: usize = chunks.iter().map(|c| c.token_count).sum();

        let proto_chunks: Vec<ProtoChunk> = chunks
            .into_iter()
            .map(|c| ProtoChunk {
                id: c.id,
                page_num: c.page_num as i32,
                text: c.text,
                token_count: c.token_count as i32,
                char_count: c.char_count as i32,
                embedding: vec![],
                images: vec![],
            })
            .collect();

        Ok(Response::new(ParseDocumentResponse {
            chunks: proto_chunks.clone(),
            metadata: Some(DocumentMetadata {
                filename: req.filename,
                content_type: req.content_type,
                size_bytes: req.content.len() as i64,
                page_count: pages.len() as i32,
                title: String::new(),
                author: String::new(),
                created_at: String::new(),
            }),
            stats: Some(ProcessingStats {
                processing_time_ms: start.elapsed().as_millis() as i64,
                total_chunks: proto_chunks.len() as i32,
                total_tokens: total_tokens as i32,
                total_images: 0,
                parser_used: "LocalPdfParser".to_string(),
            }),
        }))
    }

    type ParseDocumentStreamStream = futures::stream::Iter<std::vec::IntoIter<Result<ProtoChunk, Status>>>;

    async fn parse_document_stream(
        &self,
        _request: Request<ParseDocumentRequest>,
    ) -> Result<Response<Self::ParseDocumentStreamStream>, Status> {
        Err(Status::unimplemented("Streaming not yet implemented"))
    }

    async fn get_supported_formats(
        &self,
        _request: Request<GetSupportedFormatsRequest>,
    ) -> Result<Response<GetSupportedFormatsResponse>, Status> {
        let parser = LocalPdfParser::new();
        Ok(Response::new(GetSupportedFormatsResponse {
            extensions: parser.supported_extensions().iter().map(|s| s.to_string()).collect(),
            mime_types: parser.supported_mime_types().iter().map(|s| s.to_string()).collect(),
        }))
    }

    async fn health_check(
        &self,
        _request: Request<HealthCheckRequest>,
    ) -> Result<Response<HealthCheckResponse>, Status> {
        Ok(Response::new(HealthCheckResponse {
            status: "healthy".to_string(),
            version: "0.1.0".to_string(),
            uptime_seconds: 0,
        }))
    }
}

pub fn create_service() -> IngestionServiceServer<IngestionServiceImpl> {
    IngestionServiceServer::new(IngestionServiceImpl::default())
}

