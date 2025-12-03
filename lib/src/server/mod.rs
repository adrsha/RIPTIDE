use std::sync::{Arc, RwLock};
use crate::shared::RTShared;
use crate::server::write_libs::Writer;
use crate::server::read_libs::Reader;
use crate::server::shared_handler::SharedHandler;

pub mod read_libs;
pub mod write_libs;
pub mod shared_handler;

pub struct RTServer{
    pub reader : Reader,
    pub writer : Writer,
    pub shared_handler : SharedHandler,
    pub shared : Arc<RwLock<RTShared>>,
}

impl RTServer{
    pub fn new (shared : Arc<RwLock<RTShared>>) -> Self {
        Self {
            reader: Reader::default(),
            writer: Writer::default(),
            shared_handler : SharedHandler::default(),
            shared,
        }
    }
}
