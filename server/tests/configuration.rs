use std::path::Path;

use raicho_server::config::Config;

#[test]
fn configuration_rejects_invalid_bind_and_relative_paths() {
    assert!(Config::parse("invalid", Path::new("/data"), Path::new("/web")).is_err());
    assert!(Config::parse("127.0.0.1:8080", Path::new("data"), Path::new("/web")).is_err());
    assert!(Config::parse("127.0.0.1:8080", Path::new("/data"), Path::new("web")).is_err());
}

#[test]
fn configuration_accepts_explicit_absolute_paths() {
    let configuration =
        Config::parse("127.0.0.1:8080", Path::new("/data"), Path::new("/web")).unwrap();
    assert_eq!(configuration.bind.to_string(), "127.0.0.1:8080");
    assert_eq!(configuration.data_dir, Path::new("/data"));
    assert_eq!(configuration.web_dir, Path::new("/web"));
}

#[test]
fn startup_requires_the_diagnostic_page() {
    let directory = tempfile::tempdir().unwrap();
    let configuration =
        Config::parse("127.0.0.1:8080", directory.path(), directory.path()).unwrap();
    assert!(configuration.validate_web_assets().is_err());
    std::fs::write(directory.path().join("index.html"), "Raicho").unwrap();
    configuration.validate_web_assets().unwrap();
}
