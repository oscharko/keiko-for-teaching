// DOCX parser implementation using docx-rs

use std::io::Read;

use super::traits::{Page, Parser, ParserError};

/// Parser for DOCX (Microsoft Word) documents
pub struct DocxParser;

impl DocxParser {
    pub fn new() -> Self {
        Self
    }
}

impl Parser for DocxParser {
    fn parse<R: Read>(&self, mut reader: R) -> Result<Vec<Page>, ParserError> {
        // Read bytes from reader
        let mut data = Vec::new();
        reader.read_to_end(&mut data)
            .map_err(|e| ParserError::Io(e))?;

        // Parse DOCX file
        let docx = docx_rs::read_docx(&data)
            .map_err(|e| ParserError::ParseError(format!("Failed to parse DOCX: {}", e)))?;

        let mut pages = Vec::new();
        let mut current_text = String::new();
        let mut page_num = 1u32;

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
                            page_num,
                            text: current_text.trim().to_string(),
                            images: Vec::new(),
                        });
                        current_text.clear();
                        page_num += 1;
                    }
                }
                _ => {}
            }
        }

        // Add remaining text as last page
        if !current_text.trim().is_empty() {
            pages.push(Page {
                page_num,
                text: current_text.trim().to_string(),
                images: Vec::new(),
            });
        }

        if pages.is_empty() {
            return Err(ParserError::ParseError(
                "No text content found in DOCX".to_string(),
            ));
        }

        Ok(pages)
    }

    fn supported_extensions(&self) -> &[&str] {
        &["docx"]
    }

    fn supported_mime_types(&self) -> &[&str] {
        &["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_docx_parser_supported_extensions() {
        let parser = DocxParser::new();
        let extensions = parser.supported_extensions();
        assert!(extensions.contains(&"docx"));
    }

    #[test]
    fn test_docx_parser_supported_mime_types() {
        let parser = DocxParser::new();
        let mime_types = parser.supported_mime_types();
        assert!(mime_types.contains(&"application/vnd.openxmlformats-officedocument.wordprocessingml.document"));
    }
}

