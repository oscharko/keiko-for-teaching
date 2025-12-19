// Azure Document Intelligence parser implementation

use reqwest::Client;
use serde::Deserialize;
use std::io::Read;
use std::time::Duration;

use super::traits::{Page, Parser, ParserError};

/// Azure Document Intelligence API response
#[derive(Debug, Deserialize)]
struct AnalyzeResult {
    #[serde(rename = "analyzeResult")]
    analyze_result: Option<DocumentAnalysis>,
}

#[derive(Debug, Deserialize)]
struct DocumentAnalysis {
    pages: Option<Vec<DocumentPage>>,
    content: Option<String>,
}

#[derive(Debug, Deserialize)]
struct DocumentPage {
    #[serde(rename = "pageNumber")]
    page_number: i32,
    lines: Option<Vec<Line>>,
}

#[derive(Debug, Deserialize)]
struct Line {
    content: String,
}

/// Parser using Azure Document Intelligence (Form Recognizer)
pub struct AzureDocIntelligenceParser {
    endpoint: String,
    api_key: String,
    client: Client,
}

impl AzureDocIntelligenceParser {
    pub fn new(endpoint: String, api_key: String) -> Self {
        Self {
            endpoint,
            api_key,
            client: Client::new(),
        }
    }

    /// Analyze document using Azure Document Intelligence
    async fn analyze_document(&self, data: &[u8]) -> Result<AnalyzeResult, ParserError> {
        let url = format!("{}/formrecognizer/documentModels/prebuilt-read:analyze?api-version=2023-07-31", self.endpoint);

        // Submit document for analysis
        let response = self
            .client
            .post(&url)
            .header("Ocp-Apim-Subscription-Key", &self.api_key)
            .header("Content-Type", "application/pdf")
            .body(data.to_vec())
            .send()
            .await
            .map_err(|e| ParserError::ParseError(format!("Failed to submit document: {}", e)))?;

        if !response.status().is_success() {
            return Err(ParserError::ParseError(format!(
                "Azure API error: {}",
                response.status()
            )));
        }

        // Get operation location
        let operation_location = response
            .headers()
            .get("Operation-Location")
            .ok_or_else(|| ParserError::ParseError("No operation location".to_string()))?
            .to_str()
            .map_err(|e| ParserError::ParseError(format!("Invalid header: {}", e)))?
            .to_string();

        // Poll for results
        for _ in 0..30 {
            tokio::time::sleep(Duration::from_secs(2)).await;

            let result_response = self
                .client
                .get(&operation_location)
                .header("Ocp-Apim-Subscription-Key", &self.api_key)
                .send()
                .await
                .map_err(|e| ParserError::ParseError(format!("Failed to get results: {}", e)))?;

            if result_response.status().is_success() {
                let result: AnalyzeResult = result_response
                    .json()
                    .await
                    .map_err(|e| ParserError::ParseError(format!("Failed to parse response: {}", e)))?;

                if result.analyze_result.is_some() {
                    return Ok(result);
                }
            }
        }

        Err(ParserError::ParseError("Analysis timeout".to_string()))
    }
}

impl Parser for AzureDocIntelligenceParser {
    fn parse<R: Read>(&self, mut reader: R) -> Result<Vec<Page>, ParserError> {
        // Read bytes from reader
        let mut data = Vec::new();
        reader.read_to_end(&mut data)
            .map_err(|e| ParserError::Io(e))?;

        // Use tokio::task::block_in_place to run async code in sync context
        let result = tokio::task::block_in_place(|| {
            tokio::runtime::Handle::current().block_on(self.analyze_document(&data))
        })?;

        let analysis = result
            .analyze_result
            .ok_or_else(|| ParserError::ParseError("No analysis result".to_string()))?;

        let mut pages = Vec::new();

        if let Some(doc_pages) = analysis.pages {
            for doc_page in doc_pages {
                let mut text = String::new();

                if let Some(lines) = doc_page.lines {
                    for line in lines {
                        text.push_str(&line.content);
                        text.push('\n');
                    }
                }

                if !text.trim().is_empty() {
                    pages.push(Page {
                        page_num: doc_page.page_number as u32,
                        text: text.trim().to_string(),
                        images: Vec::new(),
                    });
                }
            }
        }

        if pages.is_empty() {
            return Err(ParserError::ParseError(
                "No pages extracted".to_string(),
            ));
        }

        Ok(pages)
    }

    fn supported_extensions(&self) -> &[&str] {
        &["pdf", "jpg", "jpeg", "png", "bmp", "tiff"]
    }

    fn supported_mime_types(&self) -> &[&str] {
        &[
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/bmp",
            "image/tiff",
        ]
    }
}

