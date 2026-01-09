// AI Auto-Wiring Bridge - Connects Rust Terminal to Python Auto-Wiring System
use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use std::process::{Command, Stdio};
use std::io::Write;
use tracing::{info, debug, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AutoWireResult {
    pub processed_command: String,
    pub suggestions: Vec<String>,
    pub agent_used: Option<String>,
    pub confidence: f32,
}

pub struct AutoWireBridge {
    python_available: bool,
    cache: std::collections::HashMap<String, AutoWireResult>,
}

impl AutoWireBridge {
    pub fn new() -> Result<Self> {
        // Check Python availability
        let python_check = Command::new("python3")
            .args(&["--version"])
            .output()
            .is_ok();

        info!("Python available: {}", python_check);

        Ok(Self {
            python_available: python_check,
            cache: std::collections::HashMap::new(),
        })
    }

    pub async fn process_command(&mut self, command: &str) -> Result<Option<AutoWireResult>> {
        if !self.python_available {
            return Ok(None);
        }

        // Check cache first
        if let Some(cached) = self.cache.get(command) {
            debug!("Using cached auto-wire result for: {}", command);
            return Ok(Some(cached.clone()));
        }

        // Process through Python auto-wiring system
        let result = self.call_python_autowire(command).await?;

        // Cache the result
        if let Some(ref res) = result {
            self.cache.insert(command.to_string(), res.clone());
        }

        Ok(result)
    }

    async fn call_python_autowire(&self, command: &str) -> Result<Option<AutoWireResult>> {
        let python_script = format!(
            r#"
import sys
import json
sys.path.insert(0, '../src')

try:
    from core.autowire import get_autowire
    from agents.base_agent import BaseAgent, AgentContext
    
    # Get auto-wire instance
    autowire = get_autowire()
    
    # Simple command processing
    command = {}
    
    # Check if it's a special command
    suggestions = []
    processed_command = command
    
    if command.startswith('ai '):
        # AI-assisted command
        suggestions.append("Using AI agent for processing")
        processed_command = command[3:]  # Remove 'ai ' prefix
    elif 'docker' in command:
        suggestions.append("Docker agent available")
    elif 'git' in command:
        suggestions.append("Git agent available")
    
    result = {{
        "processed_command": processed_command,
        "suggestions": suggestions,
        "agent_used": None,
        "confidence": 0.8
    }}
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"error": str(e)}}), file=sys.stderr)
"#,
            serde_json::to_string(command)?
        );

        let output = Command::new("python3")
            .arg("-c")
            .arg(&python_script)
            .output()
            .context("Failed to execute Python auto-wire script")?;

        if !output.status.success() {
            warn!("Python auto-wire execution failed: {}", 
                  String::from_utf8_lossy(&output.stderr));
            return Ok(None);
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        if stdout.trim().is_empty() {
            return Ok(None);
        }

        match serde_json::from_str::<AutoWireResult>(&stdout) {
            Ok(result) => {
                info!("Auto-wire result: confidence={}", result.confidence);
                Ok(Some(result))
            }
            Err(e) => {
                warn!("Failed to parse auto-wire result: {}", e);
                Ok(None)
            }
        }
    }

    pub fn service_count(&self) -> usize {
        // Query auto-wiring system for service count
        if !self.python_available {
            return 0;
        }

        let python_script = r#"
import sys
sys.path.insert(0, '../src')
try:
    from core.autowire import get_autowire
    autowire = get_autowire()
    print(len(autowire.get_registry_info()))
except:
    print(0)
"#;

        Command::new("python3")
            .arg("-c")
            .arg(python_script)
            .output()
            .ok()
            .and_then(|output| {
                String::from_utf8(output.stdout)
                    .ok()
                    .and_then(|s| s.trim().parse().ok())
            })
            .unwrap_or(0)
    }

    pub fn list_services(&self) -> Vec<String> {
        if !self.python_available {
            return vec![];
        }

        let python_script = r#"
import sys
import json
sys.path.insert(0, '../src')
try:
    from core.autowire import get_autowire
    autowire = get_autowire()
    services = list(autowire.get_registry_info().keys())
    print(json.dumps(services))
except:
    print("[]")
"#;

        Command::new("python3")
            .arg("-c")
            .arg(python_script)
            .output()
            .ok()
            .and_then(|output| {
                String::from_utf8(output.stdout).ok()
            })
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default()
    }

    pub fn clear_cache(&mut self) {
        self.cache.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_autowire_bridge_creation() {
        let bridge = AutoWireBridge::new();
        assert!(bridge.is_ok());
    }

    #[tokio::test]
    async fn test_command_processing() {
        let mut bridge = AutoWireBridge::new().unwrap();
        let result = bridge.process_command("ls -la").await;
        assert!(result.is_ok());
    }
}
