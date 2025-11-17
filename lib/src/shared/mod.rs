pub mod frames;
pub mod buffers;

use std::sync::{ LazyLock, RwLock };

pub struct Shared {
    pub frames : frames::FrameStorage,
    pub buffers : buffers::BufferStorage
}
impl Default for Shared{
    fn default() -> Self {
        Self{
            frames: frames::FrameStorage::default(),
            buffers: buffers::BufferStorage::default()
        }
    }
}

pub static SHARED: LazyLock<RwLock<Shared>> = LazyLock::new(|| RwLock::new(Shared::default()));
