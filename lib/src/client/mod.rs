pub mod windows;
use windows::RTWindow;
use eframe::egui::{self, ViewportId};
use crate::shared::{self, RTShared};


pub struct RTClient<'c> {
    pub windows:   Vec<RTWindow>,
    pub shared :   &'c RTShared,
    pub next_frame_cluster_idx: usize,

    is_alive: bool,
}


impl <'c> RTClient <'c>{
    pub fn new(shared: &'c shared::RTShared) -> Self{
        Self {
            windows : vec![RTWindow::default(String::from("Riptide Default"), 0)],
            shared,
            next_frame_cluster_idx : 0,

            is_alive: false,
        }
    }
}


impl <'c> eframe::App for RTClient <'c> {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if !self.is_alive != true {
            let frame_clusters  = &self.shared
                                            .frames
                                            .frame_clusters[self.next_frame_cluster_idx];
            let buffers = &self.shared
                                            .buffers.buffers;

            for (idx, frame) in frame_clusters.frames.iter().enumerate() {
                let content = buffers[frame.buffer_index].content.clone();
                self.windows.push(
                    RTWindow::default(content, idx)
                );
            }

            self.is_alive = true;
        }
        self.windows.iter_mut().for_each(|window| {
            ctx.show_viewport_deferred(
                ViewportId::from_hash_of(window.id),
                egui::ViewportBuilder::default()
                    .with_title("Deferred Viewport")
                    .with_inner_size([200.0, 100.0]),
                |ctx, _| {
                    egui::CentralPanel::default().show(ctx, |ui| {
                        ui.label("Data From the deferred window");
                    });
                }
            );
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.label("Hello from the root viewport");
            ui.label("adding new window");
            if ui.button("Add Window").clicked() {
                self.windows.push(RTWindow::default(String::from("New Window"), 0));
            }
        });
        println!("{}", self.windows.len());
    }
}
