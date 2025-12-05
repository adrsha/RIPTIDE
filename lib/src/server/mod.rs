use std::sync::{Arc, RwLock};
use crate::shared::RTShared;
use crate::server::write_libs::Writer;
use crate::server::read_libs::Reader;
use crate::server::session::{Session};
use std::{thread, time::Duration};

pub mod read_libs;
pub mod write_libs;
pub mod session;

pub struct RTServer{
    pub reader : Reader,
    pub writer : Writer,
    pub session : Session,
    pub shared : Arc<RwLock<RTShared>>,
}

impl RTServer{
    pub fn new (shared : Arc<RwLock<RTShared>>) -> Self {
        Self {
            reader: Reader::default(),
            writer: Writer::default(),
            session : Session::new(shared.clone()),
            shared,
        }
    }
    pub fn init() {
        loop {
                    // Do background work
                    println!("Background task running...");

                    // Sleep = near-zero CPU usage
                    thread::sleep(Duration::from_secs(60));
                }
    }
}
