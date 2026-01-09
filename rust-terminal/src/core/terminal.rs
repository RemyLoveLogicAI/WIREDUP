// Core Terminal Engine with Auto-Wiring Integration
use anyhow::{Result, Context};
use std::process::{Command, Child, Stdio};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;
use tracing::{info, error, debug};
use serde::{Deserialize, Serialize};

use crate::utils::config::Config;
use crate::ai::autowire_bridge::AutoWireBridge;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResult {
    pub command: String,
    pub output: String,
    pub error: String,
    pub exit_code: i32,
    pub duration_ms: u64,
    pub autowire_processed: bool,
}

pub struct Terminal {
    config: Config,
    shell_process: Option<Child>,
    output_buffer: Arc<Mutex<Vec<String>>>,
    command_history: Vec<String>,
    autowire_bridge: Option<AutoWireBridge>,
    tx: mpsc::Sender<CommandResult>,
    rx: mpsc::Receiver<CommandResult>,
}

impl Terminal {
    pub fn new(config: Config) -> Result<Self> {
        let (tx, rx) = mpsc::channel(100);
        
        Ok(Self {
            config,
            shell_process: None,
            output_buffer: Arc::new(Mutex::new(Vec::new())),
            command_history: Vec::new(),
            autowire_bridge: None,
            tx,
            rx,
        })
    }

    pub fn enable_autowire_integration(&mut self) -> Result<()> {
        info!("Enabling auto-wiring integration...");
        
        match AutoWireBridge::new() {
            Ok(bridge) => {
                self.autowire_bridge = Some(bridge);
                info!("✅ Auto-wiring bridge initialized");
                Ok(())
            }
            Err(e) => {
                error!("Failed to initialize auto-wiring bridge: {}", e);
                info!("⚠️  Terminal will run without auto-wiring features");
                Ok(()) // Don't fail, just warn
            }
        }
    }

    pub async fn execute_command(&mut self, command: &str) -> Result<CommandResult> {
        info!("Executing command: {}", command);
        self.command_history.push(command.to_string());

        let start = std::time::Instant::now();

        // Execute through shell
        let output = Command::new(&self.config.shell)
            .arg("-c")
            .arg(command)
            .output()
            .context("Failed to execute command")?;

        let duration = start.elapsed();

        let result = CommandResult {
            command: command.to_string(),
            output: String::from_utf8_lossy(&output.stdout).to_string(),
            error: String::from_utf8_lossy(&output.stderr).to_string(),
            exit_code: output.status.code().unwrap_or(-1),
            duration_ms: duration.as_millis() as u64,
            autowire_processed: false,
        };

        // Add to output buffer
        self.add_output(&result.output);
        if !result.error.is_empty() {
            self.add_output(&format!("Error: {}", result.error));
        }

        Ok(result)
    }

    pub async fn execute_command_with_autowire(&mut self, command: &str) -> Result<CommandResult> {
        info!("Executing command with auto-wiring: {}", command);

        // Try to process through auto-wiring first
        if let Some(bridge) = &mut self.autowire_bridge {
            match bridge.process_command(command).await {
                Ok(Some(autowire_result)) => {
                    info!("Command processed by auto-wiring system");
                    
                    // Execute the auto-wiring suggested command
                    let mut result = self.execute_command(&autowire_result.processed_command).await?;
                    result.autowire_processed = true;
                    
                    // Add auto-wiring metadata to output
                    if !autowire_result.suggestions.is_empty() {
                        self.add_output(&format!("\n💡 Auto-Wiring Suggestions: {:?}", 
                                                 autowire_result.suggestions));
                    }
                    
                    return Ok(result);
                }
                Ok(None) => {
                    debug!("No auto-wiring processing for command");
                }
                Err(e) => {
                    error!("Auto-wiring processing error: {}", e);
                }
            }
        }

        // Fallback to normal execution
        self.execute_command(command).await
    }

    pub fn add_output(&self, text: &str) {
        if let Ok(mut buffer) = self.output_buffer.lock() {
            for line in text.lines() {
                buffer.push(line.to_string());
            }
        }
    }

    pub fn get_output(&self) -> Vec<String> {
        self.output_buffer.lock()
            .map(|b| b.clone())
            .unwrap_or_default()
    }

    pub fn clear_output(&self) {
        if let Ok(mut buffer) = self.output_buffer.lock() {
            buffer.clear();
        }
    }

    pub fn get_history(&self) -> &[String] {
        &self.command_history
    }

    pub fn update_output(&mut self) -> Result<()> {
        // Check for new output from background processes
        while let Ok(result) = self.rx.try_recv() {
            self.add_output(&result.output);
        }
        Ok(())
    }

    pub fn get_autowire_status(&self) -> String {
        match &self.autowire_bridge {
            Some(bridge) => format!("✅ Connected - {} services", bridge.service_count()),
            None => "⚠️  Not connected".to_string(),
        }
    }

    pub fn get_autowire_services(&self) -> Vec<String> {
        match &self.autowire_bridge {
            Some(bridge) => bridge.list_services(),
            None => vec!["Auto-wiring not available".to_string()],
        }
    }
}

impl Drop for Terminal {
    fn drop(&mut self) {
        if let Some(mut process) = self.shell_process.take() {
            let _ = process.kill();
        }
    }
}
