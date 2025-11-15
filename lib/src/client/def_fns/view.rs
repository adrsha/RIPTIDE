use crate::{client::{ GUIEvents, GUI }, shared::SHARED};
use iced::widget::{column, text };
use iced::{Element};

pub fn view_fn(gui : &GUI ) -> Element<GUIEvents> {
    column![
        text("Hi {}"),
    ].into()
}

pub use view_fn as default;
