pub mod read_libs;
pub mod write_libs;
pub mod session;

pub struct RTServer{
    pub reader : Reader,
    pub writer : Writer,
    pub session : Session,
    pub shared : Arc<RwLock<RTShared>>,
}

use crate::{
    interfaces::enums::RiptideEvents,
    server::{
        read_libs::Reader, 
        session::Session, 
        write_libs::Writer
    }, 
    shared::RTShared
};

use std::{thread, time::Duration};
use std::sync::{Arc, RwLock};
use tokio::sync::broadcast;


impl RTServer{
    pub fn new (shared : Arc<RwLock<RTShared>>, bus: broadcast::Sender<RiptideEvents>) -> Self {
        Self {
            reader: Reader::default(),
            writer: Writer::default(),
            session : Session::new(shared.clone()),
            shared,
        }
    }
    pub fn init(&self) {
        tokio::spawn(async {
            // self.rope
            // self.lsp
            // self.syntax_highlight
            // self.undo
        });
        loop {
            // Do background work
            println!("Background task running...");

            // Sleep = near-zero CPU usage
            thread::sleep(Duration::from_secs(60));
        }
    }
}
