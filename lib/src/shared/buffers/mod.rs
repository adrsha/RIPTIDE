pub struct Buffer {
    pub content : String,
}
impl Buffer{
    pub fn default() -> Self {
        Self {
            content: String::from("")
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
