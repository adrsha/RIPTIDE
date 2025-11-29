use crate::interfaces::enums::ClientEvents;
use crate::client::Client;
use iced::Subscription;

pub fn default (client : &Client) -> Subscription<ClientEvents> {
    Subscription::none()
}

