

use crate::shared::frames::Frame;

#[derive(Debug)]
pub enum RiptideEvents {
    OpenWindow,
    CloseWindow,
    CloseFrame,
}

#[derive(Debug)]
pub enum ClientEvents {
    KeyDown,
    LeftMouseBtnDown,
    RightMouseBtnDown,
    Ignored,
    WindowCloseEvent(u32),
    WindowOpenEvent(u32),
    FrameCloseEvent(usize, usize),
    FrameOpenEvent(Frame, usize)
}
