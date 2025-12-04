use std::path::{Path, PathBuf};
use std::sync::{RwLock, Arc};

use rkyv::rancor::Error;
use rkyv::util::AlignedVec;

use crate::server::read_libs::Reader;
use crate::server::Writer;
use crate::shared::{self, RTShared};

pub fn save_shared(writer : &Writer, shared : Arc<RwLock<RTShared>>) {
//clear buffer
 match shared.write() {
       Ok(mut mut_shared) => {
           //empty the buffer content
           for buffer in &mut mut_shared.buffers.buffers {
               buffer.content.clear();
           }

           //convert shared to bytes
           let shared_bytes : AlignedVec = rkyv::to_bytes::<Error>(&*mut_shared).expect("sorry"); //*smth derefereces from the rwlock
           let path = Path::new("./test");
           //write shared to file
           if let Err(e) = (writer.write)(&shared_bytes, path) {
               eprintln!("cant run method 'append' : {}", e);
           }
       },
       Err(err) => {
           eprintln!("error getting write lock in shared : {}", err);
       }
   };
}



pub fn load_shared(reader : &Reader, shared : Arc<RwLock<RTShared>>) {
    match shared.write() {
        Ok(immut_shared) => {
            let path = Path::new("./test");
            match (reader.file)(path) {
                Ok(file_content) => println!("file content : {:?}", file_content),
                Err(err) => println!("failed to open file at path : {:?}", path)
            };
            let file_content = (reader.file)(path);
        },
        Err(err) => {
            eprintln!("error getting read lock on shared : {}", err);
        }
    }
}
