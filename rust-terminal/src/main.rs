// NexTerm - Revolutionary Terminal Experience with AI Auto-Wiring
// Main entry point integrating Python AI Auto-Wiring System

use anyhow::Result;
use std::io;
use std::process::{Command, Stdio};
use tracing::{info, error, warn};
use tracing_subscriber;

mod core;
mod ui;
mod ai;
mod plugins;
mod utils;

use crate::core::terminal::Terminal;
use crate::ui::tui::TerminalUI;
use crate::utils::config::Config;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    info!("🚀 NexTerm with AI Auto-Wiring starting...");

    // Initialize AI Auto-Wiring System
    info!("Initializing AI Auto-Wiring Engine...");
    let autowire_status = initialize_autowire_system().await?;
    info!("✅ Auto-Wiring Engine: {}", autowire_status);

    // Load configuration
    let config = Config::load()?;
    info!("Configuration loaded");

    // Parse command line arguments
    let args = parse_args();

    // Initialize terminal with auto-wiring integration
    let mut terminal = Terminal::new(config.clone())?;
    terminal.enable_autowire_integration()?;
    info!("Terminal initialized with auto-wiring");

    // Initialize UI
    let mut ui = TerminalUI::new(&config)?;
    info!("UI initialized");

    // Display welcome message with auto-wiring status
    ui.show_welcome_with_autowire(&autowire_status)?;

    // Main event loop
    match run_terminal(&mut terminal, &mut ui).await {
        Ok(_) => {
            info!("NexTerm shutting down gracefully");
            shutdown_autowire_system().await?;
            Ok(())
        }
        Err(e) => {
            error!("Error in main loop: {}", e);
            shutdown_autowire_system().await?;
            Err(e)
        }
    }
}

async fn initialize_autowire_system() -> Result<String> {
    // Check if Python auto-wiring system is available
    let python_check = Command::new("python3")
        .args(&["-c", "import sys; print(sys.version)"])
        .output();

    match python_check {
        Ok(output) if output.status.success() => {
            info!("Python detected: {}", String::from_utf8_lossy(&output.stdout).trim());
            
            // Try to import and initialize the auto-wiring system
            let autowire_init = Command::new("python3")
                .args(&[
                    "-c",
                    r#"
import sys
sys.path.insert(0, '../src')
from core.autowire import get_autowire
autowire = get_autowire()
print(f"Auto-Wire initialized with {len(autowire.get_registry_info())} components")
                    "#
                ])
                .output()?;

            if autowire_init.status.success() {
                let status = String::from_utf8_lossy(&autowire_init.stdout).trim().to_string();
                Ok(status)
            } else {
                warn!("Auto-wiring system not initialized: {}", 
                      String::from_utf8_lossy(&autowire_init.stderr));
                Ok("Auto-wiring available in fallback mode".to_string())
            }
        }
        _ => {
            warn!("Python not available, auto-wiring disabled");
            Ok("Auto-wiring disabled (Python not found)".to_string())
        }
    }
}

async fn shutdown_autowire_system() -> Result<()> {
    info!("Shutting down auto-wiring system...");
    // Cleanup auto-wiring resources
    Ok(())
}

async fn run_terminal(terminal: &mut Terminal, ui: &mut TerminalUI) -> Result<()> {
    use crossterm::event::{self, Event, KeyCode, KeyModifiers};
    use std::time::Duration;

    loop {
        // Render UI
        ui.render(terminal)?;

        // Handle events
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                match (key.code, key.modifiers) {
                    // Exit
                    (KeyCode::Char('c'), KeyModifiers::CONTROL) => {
                        if ui.confirm_exit()? {
                            break;
                        }
                    }
                    (KeyCode::Char('d'), KeyModifiers::CONTROL) => {
                        // EOF - exit if input is empty
                        if ui.is_input_empty() {
                            break;
                        }
                    }

                    // Tab management
                    (KeyCode::Char('t'), KeyModifiers::CONTROL) => {
                        ui.new_tab()?;
                    }
                    (KeyCode::Char('w'), KeyModifiers::CONTROL) => {
                        ui.close_tab()?;
                    }
                    (KeyCode::Tab, KeyModifiers::CONTROL) => {
                        ui.next_tab()?;
                    }

                    // Pane management
                    (KeyCode::Char('d'), KeyModifiers::CONTROL | KeyModifiers::SHIFT) => {
                        ui.split_pane_vertical()?;
                    }
                    (KeyCode::Char('h'), KeyModifiers::CONTROL | KeyModifiers::SHIFT) => {
                        ui.split_pane_horizontal()?;
                    }

                    // Features
                    (KeyCode::Char('f'), KeyModifiers::CONTROL) => {
                        ui.open_fuzzy_finder()?;
                    }
                    (KeyCode::Char('r'), KeyModifiers::CONTROL) => {
                        ui.open_history()?;
                    }
                    (KeyCode::Char('g'), KeyModifiers::CONTROL) => {
                        ui.open_git_status()?;
                    }
                    (KeyCode::Char(' '), KeyModifiers::CONTROL) => {
                        // AI suggestions using auto-wiring system
                        ui.show_ai_suggestions_with_autowire()?;
                    }

                    // Auto-wiring features
                    (KeyCode::Char('a'), KeyModifiers::CONTROL) => {
                        ui.show_autowire_status()?;
                    }
                    (KeyCode::Char('s'), KeyModifiers::CONTROL) => {
                        ui.show_autowire_services()?;
                    }

                    // Command input
                    (KeyCode::Enter, _) => {
                        let command = ui.get_input();
                        if !command.is_empty() {
                            // Execute through auto-wiring system if available
                            terminal.execute_command_with_autowire(&command).await?;
                            ui.clear_input();
                        }
                    }
                    (KeyCode::Char(c), _) => {
                        ui.input_char(c);
                    }
                    (KeyCode::Backspace, _) => {
                        ui.input_backspace();
                    }

                    // Navigation
                    (KeyCode::Up, _) => {
                        ui.history_previous();
                    }
                    (KeyCode::Down, _) => {
                        ui.history_next();
                    }
                    (KeyCode::Left, _) => {
                        ui.cursor_left();
                    }
                    (KeyCode::Right, _) => {
                        ui.cursor_right();
                    }

                    _ => {}
                }
            }
        }

        // Update terminal output
        terminal.update_output()?;
    }

    Ok(())
}

fn parse_args() -> Args {
    // Simple argument parsing
    // In production, use clap or structopt
    Args {
        shell: std::env::var("SHELL").unwrap_or_else(|_| "/bin/bash".to_string()),
        config: None,
        ai_enabled: std::env::var("NEXTERM_AI").is_ok(),
        autowire_enabled: std::env::var("NEXTERM_AUTOWIRE").unwrap_or_else(|_| "true".to_string()) == "true",
    }
}

#[derive(Debug)]
struct Args {
    shell: String,
    config: Option<String>,
    ai_enabled: bool,
    autowire_enabled: bool,
}
