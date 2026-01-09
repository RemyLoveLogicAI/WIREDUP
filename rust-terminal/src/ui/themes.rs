// Theme system
pub struct Theme {
    pub name: String,
}

impl Theme {
    pub fn load(name: &str) -> Self {
        Self {
            name: name.to_string(),
        }
    }
}
