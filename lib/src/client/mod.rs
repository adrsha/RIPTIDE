pub mod windows;
use windows::RTWindow;
use eframe::egui::{self, ViewportId};
use crate::shared::{self, RTShared};
use std::sync::{Arc, RwLock};


pub struct RTClient {
    pub windows:   Vec<RTWindow>,
    pub shared :   Arc<RwLock<RTShared>>,
    pub next_frame_cluster_idx: usize,

    is_alive: bool,
}


impl RTClient {
    pub fn new(shared: Arc<RwLock<shared::RTShared>>) -> Self{
        Self {
            windows : vec![RTWindow::default(String::from("Riptide Default"), 0)],
            shared,
            next_frame_cluster_idx : 0,

            is_alive: false,
        }
    }
}


impl eframe::App for RTClient {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if !self.is_alive != true {
            let frame_clusters  = &self.shared.read().expect("Cannot read shared data")
                                            .frames
                                            .frame_clusters[self.next_frame_cluster_idx];
            let buffers = &self.shared.read().expect("Cannot read shared data")
                                            .buffers.buffers;

            for (idx, frame) in frame_clusters.frames.iter().enumerate() {
                let content = buffers[frame.buffer_index].content.clone();
                self.windows.push(
                    RTWindow::default(content, idx)
                );
            }

            self.is_alive = true;
        }
        for idx in 0..self.windows.iter().len(){
            ctx.show_viewport_deferred(
                ViewportId::from_hash_of(self.windows[idx].id),
                egui::ViewportBuilder::default()
                    .with_title("Deferred Viewport")
                    .with_inner_size([200.0, 100.0]),
                |ctx, _| {
                    egui::CentralPanel::default().show(ctx, |ui| {
                        if ctx.input(|i| i.viewport().close_requested()) {
                            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                            return;
                        }
                        ui.label("Data From the deferred window");
                    });
                }
            );
        };

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.label("Hello from the root viewport");
            ui.label("adding new window");
            if ui.button("Add Window").clicked() {
                self.windows.push(RTWindow::default(String::from("New Window"), 0));
            }
        });

    }
}
