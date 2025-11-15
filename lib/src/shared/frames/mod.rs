pub enum FramePositionType {
    Fixed,
    Absolute
}
pub struct Coordinates {
    pub x: i32,
    pub y: i32
}


pub struct Frame {
    pub position_type: FramePositionType,
    pub position: Coordinates,
}

impl Frame {
    pub fn default() -> Self{
        Self {
            position_type : FramePositionType::Fixed,
            position: Coordinates { x : 0, y : 0 },
        }
    }
}


pub struct FrameCluster {
    pub frames : Vec<Frame>
}

impl FrameCluster {
    pub fn default() -> Self {
        Self { 
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
