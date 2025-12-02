pub mod client;
pub mod server;
pub mod shared;
pub mod interfaces {
    pub mod enums;
}

use eframe::egui;

pub struct Libs {
    pub client : client::Client,
}

impl Default for Libs {
    fn default() -> Self {
        Self {
            client : client::Client::default(),
        }
    }
}


pub fn run_riptide(libs : Libs) -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([320.0, 240.0]),
        ..Default::default()
    };
    eframe::run_native(
        "Multiple viewports",
        options,
        Box::new(|_cc| Ok(Box::<client::Client>::default())),
    )
}
