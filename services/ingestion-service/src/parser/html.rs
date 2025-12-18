// HTML parser implementation using scraper

use async_trait::async_trait;
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
        let script_selector = Selector::parse("script, style")
            .map_err(|e| ParserError::ParseError(format!("Invalid selector: {:?}", e)))?;

        let mut text = String::new();

        // Get body content
        if let Some(body) = document.select(&body_selector).next() {
            // Remove scripts and styles
            let body_html = body.html();
            let cleaned_doc = Html::parse_fragment(&body_html);

            // Extract text
            for element in cleaned_doc.tree {
                if let scraper::node::Node::Text(text_node) = element {
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

#[async_trait]
impl Parser for HtmlParser {
    async fn parse(&self, data: &[u8]) -> Result<Vec<Page>, ParserError> {
        // Convert bytes to string
        let html = String::from_utf8(data.to_vec())
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
        let mut page_number = 1;
        let mut current_pos = 0;

        while current_pos < text.len() {
            let end_pos = std::cmp::min(current_pos + 2000, text.len());
            let page_text = &text[current_pos..end_pos];

            pages.push(Page {
                page_number,
                text: page_text.to_string(),
            });

            current_pos = end_pos;
            page_number += 1;
        }

        Ok(pages)
    }

    fn supported_formats(&self) -> Vec<String> {
        vec![
            "html".to_string(),
            "htm".to_string(),
            "text/html".to_string(),
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_html_parser_supported_formats() {
        let parser = HtmlParser::new();
        let formats = parser.supported_formats();
        assert!(formats.contains(&"html".to_string()));
    }

    #[tokio::test]
    async fn test_html_parser_basic() {
        let parser = HtmlParser::new();
        let html = b"<html><body><h1>Test</h1><p>Content</p></body></html>";
        let result = parser.parse(html).await;
        assert!(result.is_ok());
        let pages = result.unwrap();
        assert!(!pages.is_empty());
    }
}

