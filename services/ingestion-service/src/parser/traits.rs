use std::io::Read;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ParserError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("PDF parsing error: {0}")]
    PdfParse(String),
    #[error("Parse error: {0}")]
    ParseError(String),
    #[error("Unsupported format: {0}")]
    UnsupportedFormat(String),
}

#[derive(Debug, Clone)]
pub struct Page {
    pub page_num: u32,
    pub text: String,
    pub images: Vec<Image>,
}

#[derive(Debug, Clone)]
pub struct Image {
    pub id: String,
    pub data: Vec<u8>,
    pub content_type: String,
}

pub trait Parser: Send + Sync {
    fn parse<R: Read>(&self, reader: R) -> Result<Vec<Page>, ParserError>;
    fn supported_extensions(&self) -> &[&str];
    fn supported_mime_types(&self) -> &[&str];
}

