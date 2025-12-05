use std::path::Path;
use std::io::Result;

use crate::server::session::Session;
use crate::server::Writer;

pub fn unload(session : &Session, writer : &Writer) -> Result<()> {
    let mut mut_shared = session.shared.write().unwrap();
    //empty the buffer content
    for buffer in &mut mut_shared.buffers.buffers {
        buffer.content.clear();
    }

    //convert shared to bytes
    let serialized_shared = bitcode::encode(&*mut_shared);

    let path = Path::new("./test.txt");

    //write shared to file
    if let Err(e) = (writer.write)(&serialized_shared, path, false) {
        eprintln!("cant run method 'append' : {}", e);
    }
    Ok(())
}
