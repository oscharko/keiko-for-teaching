// HTML parser implementation using scraper

use std::io::Read;
use scraper::{Html, Selector};

use super::traits::{Page, Parser, ParserError};

/// Parser for HTML documents
pub struct HtmlParser;

impl HtmlParser {
    pub fn new() -> Self {
        Self
    }

    /// Extract text from HTML, removing scripts and styles
    fn extract_text(&self, html: &str) -> Result<String, ParserError> {
        let document = Html::parse_document(html);

        // Remove script and style tags
        let body_selector = Selector::parse("body")
            .map_err(|e| ParserError::ParseError(format!("Invalid selector: {:?}", e)))?;

        let mut text = String::new();

        // Get body content
        if let Some(body) = document.select(&body_selector).next() {
            // Remove scripts and styles
            let body_html = body.html();
            let cleaned_doc = Html::parse_fragment(&body_html);

            // Extract text
            for element in cleaned_doc.tree.nodes() {
                if let scraper::node::Node::Text(text_node) = element.value() {
                    let content = text_node.text.trim();
                    if !content.is_empty() {
                        text.push_str(content);
                        text.push(' ');
                    }
                }
            }
        } else {
            // Fallback: extract all text
            for text_node in document.tree.nodes() {
                if let scraper::node::Node::Text(text_node) = text_node.value() {
                    let content = text_node.text.trim();
                    if !content.is_empty() {
                        text.push_str(content);
                        text.push(' ');
                    }
                }
            }
        }

        Ok(text.trim().to_string())
    }
}

impl Parser for HtmlParser {
    fn parse<R: Read>(&self, mut reader: R) -> Result<Vec<Page>, ParserError> {
        // Read bytes from reader
        let mut data = Vec::new();
        reader.read_to_end(&mut data)
            .map_err(|e| ParserError::Io(e))?;

        // Convert bytes to string
        let html = String::from_utf8(data)
            .map_err(|e| ParserError::ParseError(format!("Invalid UTF-8: {}", e)))?;

        // Extract text
        let text = self.extract_text(&html)?;

        if text.is_empty() {
            return Err(ParserError::ParseError(
                "No text content found in HTML".to_string(),
            ));
        }

        // Split into pages (every ~2000 characters)
        let mut pages = Vec::new();
        let mut page_num = 1u32;
        let mut current_pos = 0;

        while current_pos < text.len() {
            let end_pos = std::cmp::min(current_pos + 2000, text.len());
            let page_text = &text[current_pos..end_pos];

            pages.push(Page {
                page_num,
                text: page_text.to_string(),
                images: Vec::new(),
            });

            current_pos = end_pos;
            page_num += 1;
        }

        Ok(pages)
    }

    fn supported_extensions(&self) -> &[&str] {
        &["html", "htm"]
    }

    fn supported_mime_types(&self) -> &[&str] {
        &["text/html"]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn test_html_parser_supported_extensions() {
        let parser = HtmlParser::new();
        let extensions = parser.supported_extensions();
        assert!(extensions.contains(&"html"));
        assert!(extensions.contains(&"htm"));
    }

    #[test]
    fn test_html_parser_supported_mime_types() {
        let parser = HtmlParser::new();
        let mime_types = parser.supported_mime_types();
        assert!(mime_types.contains(&"text/html"));
    }

    #[test]
    fn test_html_parser_basic() {
        let parser = HtmlParser::new();
        let html = b"<html><body><h1>Test</h1><p>Content</p></body></html>";
        let cursor = Cursor::new(html.to_vec());
        let result = parser.parse(cursor);
        assert!(result.is_ok());
        let pages = result.unwrap();
        assert!(!pages.is_empty());
    }
}

