use eframe::egui::{self, Context, Window};

#[derive(Clone)]
pub struct RTWindow {
    pub id: egui::Id,
    pub title: String,
    pub frame_cluster_index : usize,
    pub open: bool,
    is_open: bool,
    pub show : fn(&mut Self, &Context),
}

fn show_window(window: &mut RTWindow, ctx: &Context) {
    if window.is_open {
        return
    }
    Window::new(&window.title)
        .open(&mut window.open)
        .show(ctx, |ui| {
            ui.label(format!("Hi There"));
        });
    window.is_open = true;
}

impl RTWindow {
    pub fn default(
        title: String,
        frame_cluster_index: usize,
    ) -> Self {
        Self {
            id: egui::Id::new(&title),
            title,
            frame_cluster_index,
            open: true,
            is_open: false,
            show: show_window,
        }
    }
}
