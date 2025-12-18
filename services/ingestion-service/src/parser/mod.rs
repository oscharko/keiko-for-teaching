mod azure_doc_intelligence;
mod docx;
mod html;
mod local_pdf;
mod traits;

pub use azure_doc_intelligence::AzureDocIntelligenceParser;
pub use docx::DocxParser;
pub use html::HtmlParser;
pub use local_pdf::LocalPdfParser;
pub use traits::{Page, Parser, ParserError};

