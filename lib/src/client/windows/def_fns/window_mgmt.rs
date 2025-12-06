use egui::{CentralPanel, Frame, Vec2, Color32, CornerRadius};
use eframe::egui;
use crate::{client::{RTClient, RTWindow, ViewportId}, shared::RTShared};

pub fn load_side_windows(client: &mut RTClient) {
    let rd_shared      = &client.shared.read().expect("cannot read Shared");
    let frame_clusters = &rd_shared.frames.read().expect("Cannot read frames").frame_clusters[client.next_frame_cluster_idx];
    let buffers        = &rd_shared.buffers.read().expect("Cannot read buffers").buffers;

    for (idx, frame) in frame_clusters.frames.iter().enumerate() {
        let content = buffers[frame.buffer_index].content.clone();
        client.side_windows.write()
            .expect("Error trying to write onto windows").push(
                RTWindow::default(content, idx)
            );
    }
}

pub fn create_side_windows(client: &mut RTClient, ctx: &egui::Context) {
    let mut writable_windows =  client.side_windows.write().expect("Error trying to write onto windows");

    for (idx, mut window) in writable_windows.iter_mut().enumerate() {
        (client.events.on_window_open)(&mut window);

        let arced_windows = client.side_windows.clone();
        let arced_shared = client.shared.clone();

        ctx.show_viewport_deferred(
            ViewportId::from_hash_of(window.id),
            client.viewport_options.clone(),

            move |ctx, _| {
                egui::CentralPanel::default().show(ctx, |ui| {
                    let mut rw_windows = arced_windows.write().expect("Windows not resolved");

                    if ctx.input(|i| i.viewport().close_requested()) {
                        rw_windows.remove(idx);
                        return;
                    }

                    let rw_shared = arced_shared.write().expect("Shared not resolved");
                    let frame_cluster = &rw_shared.frames.read()
                        .expect("Cannot read frames").frame_clusters[rw_windows[idx].frame_cluster_index];
                    let buffers = &mut rw_shared.buffers.write()
                        .expect("Cannot read buffers").buffers;

                    ui.vertical(|ui| {
                        for frame_data in &frame_cluster.frames {
                            let frame = Frame::new() 
                                .fill(Color32::from_rgb(30, 30, 30)) 
                                .stroke(egui::Stroke::new(1.0, Color32::BLACK))
                                .corner_radius(CornerRadius::same(6))
                                .inner_margin(egui::Margin::same(8));

                            frame.show(ui, |ui| {
                                let response = ui.add_sized(
                                    ui.available_size(),
                                    egui::TextEdit::multiline(&mut buffers[frame_data.buffer_index].content)
                                        .code_editor()
                                        .lock_focus(true)
                                        .frame(false),
                                );
                            });

                            ui.add_space(10.0);
                        }
                    });
                });
            }
        );
    };
}

pub fn create_main_window(client: &mut RTClient, ctx: &egui::Context) {
    egui::CentralPanel::default().show(ctx, |ui| {
        if ui.button("Add Window").clicked() {
            client.side_windows.write().expect("Error trying to write onto windows")
                .push(RTWindow::default(String::from("New Window"), 0));
        }
        if ui.button("Remove Window").clicked() {
            client.side_windows.write().expect("Error trying to write onto windows")
                .remove(0);
        }
    });
}
