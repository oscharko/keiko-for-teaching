use axum::{
    extract::Multipart,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::Serialize;
use std::io::Cursor;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

use crate::parser::{LocalPdfParser, Parser};
use crate::splitter::{Chunk, SentenceTextSplitter, TextSplitter};

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    service: String,
    version: String,
}

#[derive(Serialize)]
struct ParseResponse {
    chunks: Vec<Chunk>,
    metadata: DocumentMetadata,
    stats: ProcessingStats,
}

#[derive(Serialize)]
struct DocumentMetadata {
    filename: String,
    content_type: String,
    size_bytes: usize,
    page_count: usize,
}

#[derive(Serialize)]
struct ProcessingStats {
    processing_time_ms: u64,
    total_chunks: usize,
    total_tokens: usize,
}

#[derive(Serialize)]
struct SupportedFormatsResponse {
    extensions: Vec<String>,
    mime_types: Vec<String>,
}

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy".to_string(),
        service: "ingestion-service".to_string(),
        version: "0.1.0".to_string(),
    })
}

async fn supported_formats() -> Json<SupportedFormatsResponse> {
    let parser = LocalPdfParser::new();
    Json(SupportedFormatsResponse {
        extensions: parser.supported_extensions().iter().map(|s| s.to_string()).collect(),
        mime_types: parser.supported_mime_types().iter().map(|s| s.to_string()).collect(),
    })
}

async fn parse_document(mut multipart: Multipart) -> Result<Json<ParseResponse>, StatusCode> {
    let start = std::time::Instant::now();

    let mut file_data: Option<Vec<u8>> = None;
    let mut filename = String::new();
    let mut content_type = String::new();

    while let Ok(Some(field)) = multipart.next_field().await {
        if field.name() == Some("file") {
            filename = field.file_name().unwrap_or("unknown").to_string();
            content_type = field.content_type().unwrap_or("application/octet-stream").to_string();
            if let Ok(bytes) = field.bytes().await {
                file_data = Some(bytes.to_vec());
            }
        }
    }

    let data = file_data.ok_or(StatusCode::BAD_REQUEST)?;
    let size_bytes = data.len();

    let parser = LocalPdfParser::new();
    let pages = parser.parse(Cursor::new(&data)).map_err(|_| StatusCode::UNPROCESSABLE_ENTITY)?;

    let splitter = SentenceTextSplitter::new(500, 10);
    let chunks = splitter.split(&pages);

    let total_tokens: usize = chunks.iter().map(|c| c.token_count).sum();

    Ok(Json(ParseResponse {
        chunks: chunks.clone(),
        metadata: DocumentMetadata {
            filename,
            content_type,
            size_bytes,
            page_count: pages.len(),
        },
        stats: ProcessingStats {
            processing_time_ms: start.elapsed().as_millis() as u64,
            total_chunks: chunks.len(),
            total_tokens,
        },
    }))
}

pub fn create_router() -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    Router::new()
        .route("/health", get(health))
        .route("/api/formats", get(supported_formats))
        .route("/api/parse", post(parse_document))
        .layer(cors)
        .layer(TraceLayer::new_for_http())
}

