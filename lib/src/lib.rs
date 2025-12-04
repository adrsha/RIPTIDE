pub mod client;
pub mod server;
pub mod shared;
pub mod interfaces {
    pub mod enums;
}

use std::sync::{Arc, RwLock};
use eframe::egui::{self, X11WindowType};

pub struct Libs {
    pub client: client::RTClient,
    pub server : server::RTServer
}

impl Libs {
    pub fn new(shared: Arc<RwLock<shared::RTShared>>) -> Self {
        Self {
            client: client::RTClient::new(shared.clone()),
            server : server::RTServer::new(shared.clone())
        }
    }
}


pub fn run_riptide(libs : Libs) -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("Riptide")
            .with_active(true)
            .with_app_id("riptide")
            .with_resizable(true)
            .with_maximized(false)
            .with_taskbar(false)
            .with_close_button(false)
            .with_decorations(false)
            .with_window_type(X11WindowType::Normal)
            .with_transparent(false)
            .with_titlebar_buttons_shown(false)
            .with_has_shadow(true)
            .with_visible(true)
            .with_inner_size([320.0, 240.0]),
        ..Default::default()
    };

    eframe::run_native(
        "Multiple viewports", options,
        Box::new(|_cc| Ok(Box::new(libs.client)))
    )
}
