use crate::{client::{ ClientEvents, Client }, shared::SHARED};
use iced::Subscription;

pub fn subscription_fn (gui : &Client) -> Subscription<ClientEvents> {
    Subscription::none()
}

pub use subscription_fn as default;
