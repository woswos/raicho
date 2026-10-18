pub mod generated;
pub mod limits_generated;

mod decode;
mod error;
mod parse;
mod preflight;
mod schema;

pub use decode::{Phase, decode_frame};
pub use error::ContractError;
