use std::error::Error as StandardError;
use std::fmt;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug)]
pub struct Error {
    context: &'static str,
    source: Option<Box<dyn StandardError + Send + Sync>>,
}

impl Error {
    pub fn message(context: &'static str) -> Self {
        Self { context, source: None }
    }

    pub fn new(context: &'static str, source: impl StandardError + Send + Sync + 'static) -> Self {
        Self {
            context,
            source: Some(Box::new(source)),
        }
    }
}

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}", self.context)?;
        if let Some(source) = &self.source {
            write!(formatter, ": {source}")?;
        }
        Ok(())
    }
}

impl StandardError for Error {
    fn source(&self) -> Option<&(dyn StandardError + 'static)> {
        self.source.as_deref().map(|source| source as &dyn StandardError)
    }
}
