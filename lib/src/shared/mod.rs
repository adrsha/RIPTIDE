use std::sync::RwLock;

// use bitcode::{Decode, Encode};

pub mod frames;
pub mod buffers;

// #[derive(Encode, Decode)]
pub struct RTShared {
    pub frames  : RwLock<frames::FrameStorage>,
    pub buffers : RwLock<buffers::BufferStorage>
}

impl Default for RTShared{
    fn default() -> Self {
        Self{
            frames: RwLock::new(frames::FrameStorage::default()),
            buffers: RwLock::new(buffers::BufferStorage::default())
        }
    }
}
