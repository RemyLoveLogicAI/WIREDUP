// Plugin manager
use anyhow::Result;

pub struct PluginManager {
    plugins: Vec<Box<dyn Plugin>>,
}

pub trait Plugin {
    fn name(&self) -> &str;
    fn execute(&self, args: &[String]) -> Result<String>;
}

impl PluginManager {
    pub fn new() -> Self {
        Self {
            plugins: Vec::new(),
        }
    }

    pub fn register(&mut self, plugin: Box<dyn Plugin>) {
        self.plugins.push(plugin);
    }
}
