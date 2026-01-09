// Command parsing and handling
use anyhow::Result;

pub struct CommandParser;

impl CommandParser {
    pub fn new() -> Self {
        Self
    }

    pub fn parse(&self, input: &str) -> Result<ParsedCommand> {
        Ok(ParsedCommand {
            command: input.to_string(),
            args: vec![],
        })
    }
}

pub struct ParsedCommand {
    pub command: String,
    pub args: Vec<String>,
}
