use std::io::Read;
use super::traits::{Page, Parser, ParserError};

pub struct LocalPdfParser;

impl LocalPdfParser {
    pub fn new() -> Self {
        Self
    }
}

impl Default for LocalPdfParser {
    fn default() -> Self {
        Self::new()
    }
}

impl Parser for LocalPdfParser {
    fn parse<R: Read>(&self, mut reader: R) -> Result<Vec<Page>, ParserError> {
        let mut buffer = Vec::new();
        reader.read_to_end(&mut buffer)?;

        let doc = lopdf::Document::load_mem(&buffer)
            .map_err(|e| ParserError::PdfParse(e.to_string()))?;

        let mut pages = Vec::new();
        let page_count = doc.get_pages().len();

        for page_num in 1..=page_count {
            let text = pdf_extract::extract_text_from_mem(&buffer)
                .map_err(|e| ParserError::PdfParse(e.to_string()))?;

            pages.push(Page {
                page_num: page_num as u32,
                text,
                images: Vec::new(),
            });
            break; // pdf_extract extracts all pages at once
        }

        if pages.is_empty() && page_count > 0 {
            let text = pdf_extract::extract_text_from_mem(&buffer)
                .unwrap_or_default();
            pages.push(Page {
                page_num: 1,
                text,
                images: Vec::new(),
            });
        }

        Ok(pages)
    }

    fn supported_extensions(&self) -> &[&str] {
        &["pdf"]
    }

    fn supported_mime_types(&self) -> &[&str] {
        &["application/pdf"]
    }
}

