use crate::{client::{ GUIEvents, GUI }, shared::SHARED};
use iced::Subscription;

pub fn subscription_fn (gui : &GUI) -> Subscription<GUIEvents> {
    Subscription::none()
}

pub use subscription_fn as default;
