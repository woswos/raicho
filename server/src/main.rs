mod cli;
mod shutdown;

use std::process::ExitCode;
use std::sync::Arc;
use std::time::Duration;

use raicho_server::config::Config;
use raicho_server::connector::Connector;
use raicho_server::error::{Error, Result};
use raicho_server::{persistence::Database, router};
use tokio::net::TcpListener;

#[tokio::main]
async fn main() -> ExitCode {
    match run().await {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("FAIL: {error}");
            ExitCode::FAILURE
        }
    }
}

async fn run() -> Result<()> {
    let arguments: Vec<_> = std::env::args_os().skip(1).collect();
    if !arguments.is_empty() {
        return cli::run(&arguments).await;
    }
    let configuration = Config::from_environment()?;
    configuration.validate_web_assets()?;
    let database = Arc::new(Database::open(&configuration.data_dir).await?);
    let connector = Connector::new(Arc::clone(&database));
    let application = router(Arc::clone(&database), &configuration.web_dir, Arc::clone(&connector));
    let result = async {
        let listener = TcpListener::bind(configuration.bind)
            .await
            .map_err(|error| Error::new("Cannot bind HTTP listener", error))?;
        let connector_listener = TcpListener::bind(configuration.connector_bind)
            .await
            .map_err(|error| Error::new("Cannot bind connector listener", error))?;
        eprintln!("Raicho server ready");
        shutdown::serve(listener, application, connector_listener, Arc::clone(&connector)).await
    }
    .await;
    tokio::time::timeout(Duration::from_secs(5), database.close())
        .await
        .map_err(|error| Error::new("Application database shutdown timed out", error))?;
    result
}
