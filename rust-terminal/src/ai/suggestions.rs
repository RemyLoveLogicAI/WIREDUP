// AI suggestions
use anyhow::Result;

pub struct SuggestionEngine;

impl SuggestionEngine {
    pub fn new() -> Self {
        Self
    }

    pub fn get_suggestions(&self, input: &str) -> Vec<String> {
        vec![]
    }
}
