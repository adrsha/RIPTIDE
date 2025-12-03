use std::path::{Path, PathBuf};
use std::sync::{RwLock, Arc};

use rkyv::rancor::Error;
use rkyv::util::AlignedVec;

use crate::server::read_libs::Reader;
use crate::server::Writer;
use crate::shared::{self, RTShared};

pub fn save_shared(writer : &Writer, shared : Arc<RwLock<RTShared>>) {
    //clean the buffer content
    let mut mut_shared = shared.write().unwrap();
    for buffer in &mut mut_shared.buffers.buffers {
        buffer.content.clear();
    }
    //convert shared to bytes
    let shared_bytes : AlignedVec = rkyv::to_bytes::<Error>(&*mut_shared).expect("sorry"); //*smth derefereces from the rwlock
    let path = Path::new("./test");
    if let Err(e) = (writer.write)(&shared_bytes, path) {
        eprintln!("cant run method 'append' : {}", e);
    }
}

pub fn load_shared(reader : &Reader, shared : &mut RTShared) {

}
