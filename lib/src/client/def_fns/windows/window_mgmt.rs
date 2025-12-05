use eframe::egui;
use crate::client::{ViewportId, RTWindow, RTClient};

pub fn load_windows(client: &mut RTClient) {
    let rd_shared      = &client.shared.read().expect("cannot read Shared");
    let frame_clusters = &rd_shared.frames.frame_clusters[client.next_frame_cluster_idx];
    let buffers        = &rd_shared.buffers.buffers;

    for (idx, frame) in frame_clusters.frames.iter().enumerate() {
        let content = buffers[frame.buffer_index].content.clone();
        client.windows.write()
            .expect("Error trying to write onto windows").push(
                RTWindow::default(content, idx)
            );
    }
}

pub fn create_side_windows(client: &mut RTClient, ctx: &egui::Context) {
    let mut writable_windows =  client.windows.write().expect("Error trying to write onto windows");

    for (idx, mut window) in writable_windows.iter_mut().enumerate() {
        (client.events.on_window_open)(&mut window);

        let arced_windows = client.windows.clone();
        ctx.show_viewport_deferred(
            ViewportId::from_hash_of(window.id),
            client.viewport_options.clone(),
            move |ctx, _| {
                egui::CentralPanel::default().show(ctx, |ui| {
                    let mut rw_windows = arced_windows.write().expect("Remaining windows not resolved");
                    if ctx.input(|i| i.viewport().close_requested()) {
                        rw_windows.remove(idx);
                        return;
                    }
                    ui.label("Data From the deferred window");
                });
            }
        );
    };
}

pub fn create_main_window(client: &mut RTClient, ctx: &egui::Context) {
    egui::CentralPanel::default().show(ctx, |ui| {
        if ui.button("Add Window").clicked() {
            client.windows.write().expect("Error trying to write onto windows")
                .push(RTWindow::default(String::from("New Window"), 0));
        }
        if ui.button("Remove Window").clicked() {
            client.windows.write().expect("Error trying to write onto windows")
                .remove(0);
        }
    });
}
