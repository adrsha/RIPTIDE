#[derive(Debug)]
pub enum FramePositionType {
    Fixed,
    Absolute
}
#[derive(Debug)]
pub struct Coordinates {
    pub x: i32,
    pub y: i32
}

#[derive(Debug)]
pub struct Frame {
    pub position_type: FramePositionType,
    pub position: Coordinates,
    pub buffer_index: usize
}

impl Frame {
    pub fn default() -> Self{
        Self {
            position_type : FramePositionType::Fixed,
            position: Coordinates { x : 0, y : 0 },
            buffer_index: 0,
        }
    }
}


pub struct FrameCluster {
    pub is_visible: bool,
    pub frames : Vec<Frame>
}

impl FrameCluster {
    pub fn default() -> Self {
        Self {
            is_visible: false,
            frames : vec![Frame::default()]
        }
    }
}


pub struct FrameStorage {
    pub frame_clusters : Vec<FrameCluster>
}

impl FrameStorage {
    pub fn default() -> Self {
        Self {
            frame_clusters: vec![ FrameCluster::default() ]
        }
    }
}
