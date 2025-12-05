use eframe::egui;

#[derive(Clone)]
pub struct RTWindow {
    pub id: egui::Id,
    pub title: String,
    pub frame_cluster_index : usize,
    pub marked_for_removal: bool,
    pub open: bool,
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
            marked_for_removal: false,
            open: false,
        }
    }
}
