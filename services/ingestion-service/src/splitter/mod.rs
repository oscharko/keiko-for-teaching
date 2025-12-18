mod sentence;

pub use sentence::SentenceTextSplitter;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Chunk {
    pub id: String,
    pub page_num: u32,
    pub text: String,
    pub token_count: usize,
    pub char_count: usize,
}

pub trait TextSplitter: Send + Sync {
    fn split(&self, pages: &[crate::parser::Page]) -> Vec<Chunk>;
}

