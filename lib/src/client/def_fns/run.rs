use crate::client::RTClient;

pub fn run_ui(client: RTClient) -> eframe::Result{
    let options = eframe::NativeOptions {
        viewport: client.viewport_options.clone(),
        hardware_acceleration: eframe::HardwareAcceleration::Preferred,
        ..Default::default()
    };

    eframe::run_native(
        "Multiple viewports", options,
        Box::new(|_cc| Ok(Box::new(client)))
    )
}
