pub(crate) fn random_hex<const BYTES: usize>() -> Result<String, getrandom::Error> {
    let mut bytes = [0u8; BYTES];
    getrandom::fill(&mut bytes)?;
    Ok(bytes.iter().map(|byte| format!("{byte:02x}")).collect())
}
