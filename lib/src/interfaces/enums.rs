use iced::window;

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
    WindowCloseEvent(window::Id),
    WindowOpenEvent(window::Id),
    FrameCloseEvent(usize, usize),
    FrameOpenEvent(Frame, usize)
}
