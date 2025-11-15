pub mod frames;
pub mod buffers;

use std::sync::{ LazyLock, RwLock };

pub struct Shared {
    frames : frames::FrameStorage,
    buffers : buffers::BufferStorage
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
