// Terminal UI with Auto-Wiring Integration
use anyhow::Result;
use crossterm::{
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span, Text},
    widgets::{Block, Borders, List, ListItem, Paragraph, Tabs},
    Frame, Terminal as RatatuiTerminal,
};
use std::io;

use crate::core::terminal::Terminal;
use crate::utils::config::Config;

pub struct TerminalUI {
    terminal: RatatuiTerminal<CrosstermBackend<io::Stdout>>,
    input_buffer: String,
    cursor_pos: usize,
    history_index: Option<usize>,
    active_tab: usize,
    tabs: Vec<String>,
    show_help: bool,
    show_autowire_panel: bool,
}

impl TerminalUI {
    pub fn new(config: &Config) -> Result<Self> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen)?;
        let backend = CrosstermBackend::new(stdout);
        let terminal = RatatuiTerminal::new(backend)?;

        Ok(Self {
            terminal,
            input_buffer: String::new(),
            cursor_pos: 0,
            history_index: None,
            active_tab: 0,
            tabs: vec!["Terminal".to_string()],
            show_help: false,
            show_autowire_panel: false,
        })
    }

    pub fn show_welcome(&mut self) -> Result<()> {
        self.show_welcome_with_autowire("Auto-wiring initializing...")
    }

    pub fn show_welcome_with_autowire(&mut self, autowire_status: &str) -> Result<()> {
        let welcome_text = vec![
            "╔══════════════════════════════════════════════════════════╗",
            "║     🚀 NEXTERM - Revolutionary Terminal Experience      ║",
            "║          with AI Auto-Wiring Integration                ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
            &format!("Auto-Wiring Status: {}", autowire_status),
            "",
            "Quick Start:",
            "  • Ctrl+T        - New tab",
            "  • Ctrl+W        - Close tab",
            "  • Ctrl+F        - Fuzzy finder",
            "  • Ctrl+Space    - AI suggestions",
            "  • Ctrl+A        - Auto-wire status",
            "  • Ctrl+S        - Auto-wire services",
            "  • Ctrl+C        - Exit",
            "",
            "AI Commands:",
            "  ai <command>    - Process command through AI",
            "  autowire list   - List auto-wire services",
            "  autowire status - Show auto-wire status",
            "",
            "Type 'help' for more commands",
            "",
        ];

        for line in welcome_text {
            println!("{}", line);
        }

        std::thread::sleep(std::time::Duration::from_secs(2));
        Ok(())
    }

    pub fn render(&mut self, terminal: &Terminal) -> Result<()> {
        self.terminal.draw(|f| {
            self.draw_ui(f, terminal);
        })?;
        Ok(())
    }

    fn draw_ui(&self, f: &mut Frame, terminal: &Terminal) {
        let size = f.size();

        // Main layout
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(3),  // Tabs
                Constraint::Min(10),    // Main content
                Constraint::Length(3),  // Input
                Constraint::Length(3),  // Status bar
            ])
            .split(size);

        // Draw tabs
        self.draw_tabs(f, chunks[0]);

        // Draw main content (split if autowire panel is shown)
        if self.show_autowire_panel {
            let content_chunks = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([
                    Constraint::Percentage(70),
                    Constraint::Percentage(30),
                ])
                .split(chunks[1]);

            self.draw_output(f, terminal, content_chunks[0]);
            self.draw_autowire_panel(f, terminal, content_chunks[1]);
        } else {
            self.draw_output(f, terminal, chunks[1]);
        }

        // Draw input
        self.draw_input(f, chunks[2]);

        // Draw status bar
        self.draw_status_bar(f, terminal, chunks[3]);
    }

    fn draw_tabs(&self, f: &mut Frame, area: Rect) {
        let tab_titles: Vec<Line> = self.tabs
            .iter()
            .map(|t| Line::from(t.as_str()))
            .collect();

        let tabs = Tabs::new(tab_titles)
            .block(Block::default().borders(Borders::ALL).title("Tabs"))
            .select(self.active_tab)
            .style(Style::default().fg(Color::White))
            .highlight_style(
                Style::default()
                    .fg(Color::Yellow)
                    .add_modifier(Modifier::BOLD),
            );

        f.render_widget(tabs, area);
    }

    fn draw_output(&self, f: &mut Frame, terminal: &Terminal, area: Rect) {
        let output = terminal.get_output();
        let items: Vec<ListItem> = output
            .iter()
            .map(|line| ListItem::new(line.as_str()))
            .collect();

        let list = List::new(items)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Output")
                    .style(Style::default().fg(Color::White)),
            )
            .style(Style::default().fg(Color::Gray));

        f.render_widget(list, area);
    }

    fn draw_autowire_panel(&self, f: &mut Frame, terminal: &Terminal, area: Rect) {
        let services = terminal.get_autowire_services();
        let status = terminal.get_autowire_status();

        let text = vec![
            Line::from(vec![
                Span::styled("🔌 Auto-Wiring", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(""),
            Line::from(vec![
                Span::raw("Status: "),
                Span::styled(status, Style::default().fg(Color::Green)),
            ]),
            Line::from(""),
            Line::from(vec![
                Span::styled("Services:", Style::default().add_modifier(Modifier::BOLD)),
            ]),
        ];

        let mut all_lines = text;
        for service in services.iter().take(10) {
            all_lines.push(Line::from(vec![
                Span::raw("  • "),
                Span::styled(service, Style::default().fg(Color::Yellow)),
            ]));
        }

        if services.len() > 10 {
            all_lines.push(Line::from(format!("  ... and {} more", services.len() - 10)));
        }

        let panel = Paragraph::new(all_lines)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Auto-Wire Panel")
                    .style(Style::default().fg(Color::Cyan)),
            );

        f.render_widget(panel, area);
    }

    fn draw_input(&self, f: &mut Frame, area: Rect) {
        let input_text = format!("> {}", self.input_buffer);
        let input = Paragraph::new(input_text)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Command Input")
                    .style(Style::default().fg(Color::Green)),
            );

        f.render_widget(input, area);
    }

    fn draw_status_bar(&self, f: &mut Frame, terminal: &Terminal, area: Rect) {
        let autowire_status = terminal.get_autowire_status();
        let status_text = format!(
            " Auto-Wire: {} | Tab: {}/{} | Ctrl+H: Help ",
            autowire_status,
            self.active_tab + 1,
            self.tabs.len()
        );

        let status = Paragraph::new(status_text)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .style(Style::default().fg(Color::White)),
            )
            .style(Style::default().fg(Color::Cyan));

        f.render_widget(status, area);
    }

    // Input methods
    pub fn input_char(&mut self, c: char) {
        self.input_buffer.insert(self.cursor_pos, c);
        self.cursor_pos += 1;
    }

    pub fn input_backspace(&mut self) {
        if self.cursor_pos > 0 {
            self.cursor_pos -= 1;
            self.input_buffer.remove(self.cursor_pos);
        }
    }

    pub fn get_input(&self) -> String {
        self.input_buffer.clone()
    }

    pub fn clear_input(&mut self) {
        self.input_buffer.clear();
        self.cursor_pos = 0;
    }

    pub fn is_input_empty(&self) -> bool {
        self.input_buffer.is_empty()
    }

    // Navigation
    pub fn cursor_left(&mut self) {
        if self.cursor_pos > 0 {
            self.cursor_pos -= 1;
        }
    }

    pub fn cursor_right(&mut self) {
        if self.cursor_pos < self.input_buffer.len() {
            self.cursor_pos += 1;
        }
    }

    pub fn history_previous(&mut self) {
        // Implement history navigation
    }

    pub fn history_next(&mut self) {
        // Implement history navigation
    }

    // Tab management
    pub fn new_tab(&mut self) -> Result<()> {
        self.tabs.push(format!("Tab {}", self.tabs.len() + 1));
        self.active_tab = self.tabs.len() - 1;
        Ok(())
    }

    pub fn close_tab(&mut self) -> Result<()> {
        if self.tabs.len() > 1 {
            self.tabs.remove(self.active_tab);
            if self.active_tab >= self.tabs.len() {
                self.active_tab = self.tabs.len() - 1;
            }
        }
        Ok(())
    }

    pub fn next_tab(&mut self) -> Result<()> {
        self.active_tab = (self.active_tab + 1) % self.tabs.len();
        Ok(())
    }

    // Feature methods
    pub fn split_pane_vertical(&mut self) -> Result<()> {
        Ok(())
    }

    pub fn split_pane_horizontal(&mut self) -> Result<()> {
        Ok(())
    }

    pub fn open_fuzzy_finder(&mut self) -> Result<()> {
        Ok(())
    }

    pub fn open_history(&mut self) -> Result<()> {
        Ok(())
    }

    pub fn open_git_status(&mut self) -> Result<()> {
        Ok(())
    }

    pub fn show_ai_suggestions(&mut self) -> Result<()> {
        Ok(())
    }

    pub fn show_ai_suggestions_with_autowire(&mut self) -> Result<()> {
        self.show_autowire_panel = !self.show_autowire_panel;
        Ok(())
    }

    pub fn show_autowire_status(&mut self) -> Result<()> {
        self.show_autowire_panel = true;
        Ok(())
    }

    pub fn show_autowire_services(&mut self) -> Result<()> {
        self.show_autowire_panel = true;
        Ok(())
    }

    pub fn confirm_exit(&self) -> Result<bool> {
        // Simple confirmation - in production, show a dialog
        Ok(true)
    }
}

impl Drop for TerminalUI {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(self.terminal.backend_mut(), LeaveAlternateScreen);
        let _ = self.terminal.show_cursor();
    }
}
