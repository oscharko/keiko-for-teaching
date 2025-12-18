use super::{Chunk, TextSplitter};
use crate::parser::Page;
use tiktoken_rs::cl100k_base;
use uuid::Uuid;

pub struct SentenceTextSplitter {
    max_tokens: usize,
    overlap_tokens: usize,
}

impl SentenceTextSplitter {
    pub fn new(max_tokens: usize, overlap_percent: usize) -> Self {
        let overlap_tokens = (max_tokens * overlap_percent) / 100;
        Self {
            max_tokens,
            overlap_tokens,
        }
    }

    fn count_tokens(&self, text: &str) -> usize {
        let bpe = cl100k_base().unwrap();
        bpe.encode_with_special_tokens(text).len()
    }

    fn split_into_sentences(&self, text: &str) -> Vec<String> {
        let mut sentences = Vec::new();
        let mut current = String::new();

        for c in text.chars() {
            current.push(c);
            if c == '.' || c == '!' || c == '?' || c == '\n' {
                let trimmed = current.trim().to_string();
                if !trimmed.is_empty() {
                    sentences.push(trimmed);
                }
                current = String::new();
            }
        }

        if !current.trim().is_empty() {
            sentences.push(current.trim().to_string());
        }

        sentences
    }
}

impl TextSplitter for SentenceTextSplitter {
    fn split(&self, pages: &[Page]) -> Vec<Chunk> {
        let mut chunks = Vec::new();

        for page in pages {
            let sentences = self.split_into_sentences(&page.text);
            let mut current_chunk = String::new();
            let mut current_tokens = 0;

            for sentence in sentences {
                let sentence_tokens = self.count_tokens(&sentence);

                if current_tokens + sentence_tokens > self.max_tokens && !current_chunk.is_empty() {
                    chunks.push(Chunk {
                        id: Uuid::new_v4().to_string(),
                        page_num: page.page_num,
                        text: current_chunk.trim().to_string(),
                        token_count: current_tokens,
                        char_count: current_chunk.len(),
                    });

                    // Keep overlap
                    let words: Vec<&str> = current_chunk.split_whitespace().collect();
                    let overlap_word_count = words.len() * self.overlap_tokens / self.max_tokens;
                    current_chunk = words[words.len().saturating_sub(overlap_word_count)..].join(" ");
                    current_tokens = self.count_tokens(&current_chunk);
                }

                if !current_chunk.is_empty() {
                    current_chunk.push(' ');
                }
                current_chunk.push_str(&sentence);
                current_tokens += sentence_tokens;
            }

            if !current_chunk.trim().is_empty() {
                chunks.push(Chunk {
                    id: Uuid::new_v4().to_string(),
                    page_num: page.page_num,
                    text: current_chunk.trim().to_string(),
                    token_count: current_tokens,
                    char_count: current_chunk.len(),
                });
            }
        }

        chunks
    }
}

