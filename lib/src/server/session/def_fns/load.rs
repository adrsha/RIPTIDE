use std::path::Path;
use std::io::Result;

use crate::server::read_libs::Reader;
use crate::server::session::Session;
use crate::Libs;

// pub fn load(session : &Session, reader : &Reader) -> Result<()> {
pub fn load(libs : &Libs) -> Result<()> {
    let mut mut_shared = libs.server.session.shared.write().unwrap();

    let path = Path::new("./test.txt");
    let mmap = (libs.server.reader.file)(path)?;

    // let deserialized = bitcode::decode(&mmap_content);
    let deserialized = bitcode::decode(&mmap).unwrap();
    *mut_shared = deserialized;
    Ok(())
}
