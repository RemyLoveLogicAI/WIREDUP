// Simple example of using NexTerm

use nexterm::core::terminal::Terminal;
use nexterm::utils::config::Config;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Create configuration
    let config = Config::default();

    // Initialize terminal
    let mut terminal = Terminal::new(config)?;

    // Enable auto-wiring
    terminal.enable_autowire_integration()?;

    // Execute a simple command
    let result = terminal.execute_command("echo 'Hello from NexTerm!'").await?;
    println!("Command output: {}", result.output);

    // Execute through auto-wiring
    let result = terminal.execute_command_with_autowire("ai analyze data").await?;
    println!("Auto-wired output: {}", result.output);
    println!("Processed by auto-wire: {}", result.autowire_processed);

    Ok(())
}
