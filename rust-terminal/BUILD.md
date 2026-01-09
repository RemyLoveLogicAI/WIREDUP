# 🔧 Building NexTerm

## Prerequisites

- Rust 1.75 or later
- Python 3.8+ (for auto-wiring integration)
- Git

## Building from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/nexterm
cd nexterm

# Build in debug mode
cargo build

# Build in release mode (optimized)
cargo build --release

# Run in development
cargo run

# Install locally
cargo install --path .
```

## Running Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Run benchmarks
cargo bench
```

## Project Structure

```
nexterm/
├── src/
│   ├── main.rs                    # Entry point with auto-wiring
│   ├── core/
│   │   ├── mod.rs
│   │   ├── terminal.rs            # Terminal engine
│   │   ├── command.rs             # Command parser
│   │   └── executor.rs            # Command executor
│   ├── ui/
│   │   ├── mod.rs
│   │   ├── tui.rs                 # TUI implementation
│   │   ├── widgets.rs             # Custom widgets
│   │   └── themes.rs              # Theme system
│   ├── ai/
│   │   ├── mod.rs
│   │   ├── autowire_bridge.rs     # Python auto-wire bridge
│   │   ├── suggestions.rs         # AI suggestions
│   │   └── nlp.rs                 # NLP processing
│   ├── plugins/
│   │   ├── mod.rs
│   │   ├── manager.rs             # Plugin manager
│   │   └── builtin.rs             # Built-in plugins
│   └── utils/
│       ├── mod.rs
│       ├── config.rs              # Configuration
│       └── history.rs             # Command history
├── examples/                      # Example code
├── docs/                          # Documentation
├── Cargo.toml                     # Dependencies
└── README.md                      # Main documentation
```

## Development

### Adding New Features

1. Create a new module in the appropriate directory
2. Implement the feature with proper error handling
3. Add tests in the module
4. Update documentation

### Code Style

We follow Rust standard conventions:

```bash
# Format code
cargo fmt

# Lint code
cargo clippy

# Check for errors without building
cargo check
```

### Dependencies

Main dependencies:
- `ratatui` - Terminal UI framework
- `crossterm` - Cross-platform terminal manipulation
- `tokio` - Async runtime
- `serde` - Serialization
- `anyhow` - Error handling

## Integration with Python Auto-Wiring

NexTerm integrates with the Python AI Auto-Wiring System:

### Setup

1. Ensure Python auto-wiring system is in parent directory:
   ```
   project/
   ├── src/               # Python auto-wiring
   └── rust-terminal/     # NexTerm
   ```

2. Set environment variable:
   ```bash
   export NEXTERM_AUTOWIRE=true
   ```

3. The terminal will automatically detect and connect to the auto-wiring system

### Features

- **Command Processing**: Commands can be routed through AI agents
- **Service Discovery**: Access all registered auto-wiring services
- **AI Suggestions**: Get intelligent command suggestions
- **Agent Integration**: Execute commands through specialized agents

## Troubleshooting

### Build Errors

**Error: "failed to resolve: use of undeclared crate"**
- Solution: Run `cargo clean && cargo build`

**Error: "linking with `cc` failed"**
- Solution: Install build essentials
  ```bash
  # Ubuntu/Debian
  sudo apt-get install build-essential
  
  # macOS
  xcode-select --install
  ```

### Runtime Errors

**Auto-wiring not connecting**
- Check Python is available: `python3 --version`
- Verify auto-wiring system is in correct location
- Check logs for connection errors

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE) file.
