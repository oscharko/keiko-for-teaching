// DOCX parser implementation using docx-rs

use async_trait::async_trait;
use std::io::Cursor;

use super::traits::{Page, Parser, ParserError};

/// Parser for DOCX (Microsoft Word) documents
pub struct DocxParser;

impl DocxParser {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl Parser for DocxParser {
    async fn parse(&self, data: &[u8]) -> Result<Vec<Page>, ParserError> {
        // Parse DOCX file
        let cursor = Cursor::new(data);
        let docx = docx_rs::read_docx(&cursor)
            .map_err(|e| ParserError::ParseError(format!("Failed to parse DOCX: {}", e)))?;

        let mut pages = Vec::new();
        let mut current_text = String::new();
        let mut page_number = 1;

        // Extract text from document
        for child in docx.document.children {
            match child {
                docx_rs::DocumentChild::Paragraph(para) => {
                    let mut para_text = String::new();
                    for child in para.children {
                        if let docx_rs::ParagraphChild::Run(run) = child {
                            for child in run.children {
                                if let docx_rs::RunChild::Text(text) = child {
                                    para_text.push_str(&text.text);
                                }
                            }
                        }
                    }
                    
                    if !para_text.is_empty() {
                        current_text.push_str(&para_text);
                        current_text.push('\n');
                    }

                    // Split into pages every ~2000 characters (approximate page)
                    if current_text.len() > 2000 {
                        pages.push(Page {
                            page_number,
                            text: current_text.trim().to_string(),
                        });
                        current_text.clear();
                        page_number += 1;
                    }
                }
                _ => {}
            }
        }

        // Add remaining text as last page
        if !current_text.trim().is_empty() {
            pages.push(Page {
                page_number,
                text: current_text.trim().to_string(),
            });
        }

        if pages.is_empty() {
            return Err(ParserError::ParseError(
                "No text content found in DOCX".to_string(),
            ));
        }

        Ok(pages)
    }

    fn supported_formats(&self) -> Vec<String> {
        vec!["docx".to_string(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document".to_string()]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_docx_parser_supported_formats() {
        let parser = DocxParser::new();
        let formats = parser.supported_formats();
        assert!(formats.contains(&"docx".to_string()));
    }
}

