use std::path::PathBuf;

pub struct Buffer {
    pub content : String,
    pub file_path : PathBuf,
}

impl Buffer{
    pub fn default() -> Self {
        Self {
            content: String::from(""),
            file_path: PathBuf::new(),
        }
    }
}

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
