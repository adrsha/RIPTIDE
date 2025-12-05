pub mod client;
pub mod server;
pub mod shared;
pub mod interfaces {
    pub mod enums;
}

use std::sync::{Arc, RwLock};

pub struct Libs {
    pub client: client::RTClient,
    pub server : server::RTServer
}

impl Libs {
    pub fn new(shared: Arc<RwLock<shared::RTShared>>) -> Self {
        Self {
            client : client::RTClient::new(shared.clone()),
            server : server::RTServer::new(shared.clone())
        }
    }
}


pub fn run_riptide(libs : Libs) -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: libs.client.viewport_options.clone(),
        ..Default::default()
    };

    eframe::run_native(
        "Multiple viewports", options,
        Box::new(|_cc| Ok(Box::new(libs.client)))
    )
}
