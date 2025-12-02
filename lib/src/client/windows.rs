#[derive(Clone)]
pub struct Window {
    pub id: u32,
    pub title: &'static str,
    pub frame_cluster_index : usize,
}

impl Window {
    pub fn default(
        title: &'static str,
    ) -> Self {
        Self {
            id: 0,
            title,
            frame_cluster_index: 0,
        }
    }
}
