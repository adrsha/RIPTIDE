use std::fs;
use std::path::Path;
use std::io::{Write, Result};

pub fn init(content: &[u8], path: &Path) -> Result<()> {
    let mut file = fs::OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(path)?;

    file.write_all(content)?;
    file.sync_all()?; // Ensure durability on manual save
    Ok(())
}

pub fn append(content: &[u8], path: &Path) -> Result<()> {
    let mut file = fs::OpenOptions::new()
        .write(true)
        .append(true)
        .create(true)
        .open(path)?;

    file.write_all(content)?;
    file.sync_all()?;
    Ok(())
}
