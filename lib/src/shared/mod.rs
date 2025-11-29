pub mod frames;
pub mod buffers;

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
