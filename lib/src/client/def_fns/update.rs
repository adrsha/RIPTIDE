use crate::{client::{ ClientEvents, Client }, shared::SHARED};

pub fn update_fn(client: &mut Client, events: ClientEvents ) {
    match events {
        ClientEvents::Ignored => {}
        ClientEvents::KeyDown => {}
        ClientEvents::LeftMouseBtnDown => {},
        ClientEvents::RightMouseBtnDown => {},
        ClientEvents::Ignored => {}
    }
}

pub use update_fn as default;
