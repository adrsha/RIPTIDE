use std::path::PathBuf;
use rkyv::{Archive, Serialize, Deserialize};

#[derive(Archive, Serialize, Deserialize)]
pub struct Buffer {
    pub content : String,
    pub file_path : String,
}

impl Buffer{
    pub fn default() -> Self {
        Self {
            content: String::from(""),
            file_path: String::new(),
        }
    }
}

#[derive(Archive, Serialize, Deserialize)]
pub struct BufferStorage {
    pub buffers : Vec<Buffer>,
}

impl BufferStorage {
    pub fn default() -> Self {
        Self {
            buffers: vec![Buffer::default()]
        }
    }
}
