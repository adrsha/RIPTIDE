pub mod frames;
pub mod buffers;

pub struct RTShared {
    pub frames : frames::FrameStorage,
    pub buffers : buffers::BufferStorage
}

impl Default for RTShared{
    fn default() -> Self {
        Self{
            frames: frames::FrameStorage::default(),
            buffers: buffers::BufferStorage::default()
        }
    }
}
