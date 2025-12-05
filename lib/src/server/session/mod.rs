mod def_fns {
    pub mod load;
    pub mod unload;
}

use std::sync::{RwLock, Arc};

use std::io::Result;
use crate::server::read_libs::Reader;
use crate::server::Writer;
use crate::shared::RTShared;
use crate::Libs;

pub struct Session {
    pub unload : fn(&Self, writer : &Writer) -> Result<()>,
    pub load : fn(&Libs) -> Result<()>,
    pub shared : Arc<RwLock<RTShared>>,
}

impl Session {
    pub fn new (shared : Arc<RwLock<RTShared>>) -> Self {
        Self  {
            unload : def_fns::unload::unload,
            load : def_fns::load::load,
            shared,
        }
    }
}
