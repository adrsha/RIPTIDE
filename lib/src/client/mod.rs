pub mod windows;
use windows::Window;
use crate::shared::Shared;

use eframe::egui::{self, pos2};

#[derive(Default)]
pub struct Client {
    pub windows:   Vec<Window>,
    pub shared :   Shared,
}

impl Client {
    pub fn default() -> Self {
        Self {
            windows: vec![
                Window::default("Window"),
            ],
            shared: Shared::default(),
        }
    }
}

impl eframe::App for Client {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.label("Hello from the root viewport");
        });
        // for window in windows {
            ctx.show_viewport_immediate(
                egui::ViewportId::from_hash_of("riptide"),
                egui::ViewportBuilder::default()
                    // .with_position(pos2(x, y))
                    .with_title("Viewport")
                .with_inner_size([200.0, 100.0]),
                |ctx, _| {
                    egui::CentralPanel::default().show(ctx, |ui| {
                        ui.label("Hello from deferred viewport");
                    });
                }
            )
        // }
    }
}
