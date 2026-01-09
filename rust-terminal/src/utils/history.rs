// Command history
use anyhow::Result;

pub struct History {
    entries: Vec<String>,
}

impl History {
    pub fn new() -> Self {
        Self {
            entries: Vec::new(),
        }
    }

    pub fn add(&mut self, command: String) {
        self.entries.push(command);
    }

    pub fn get_all(&self) -> &[String] {
        &self.entries
    }
}
