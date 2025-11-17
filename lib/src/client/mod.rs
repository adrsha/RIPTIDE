use iced::{application, Element, Subscription};

pub mod def_fns{
    pub mod view;
    pub mod update;
    pub mod subscribe;
}

#[derive(Debug)]
pub enum ClientEvents {
    KeyDown,
    LeftMouseBtnDown,
    RightMouseBtnDown,
    Ignored
}

fn init (
    client: &Client,
) -> iced::Result {
    let application
        = application("RIPTIDE", client.update, client.view);
    application.subscription(client.subscribe).run()
}

pub struct Client {
    pub update:       fn(&mut Client, ClientEvents),
    pub view:         fn(&Client) -> Element<ClientEvents>,
    pub subscribe:    fn(&Client) -> Subscription<ClientEvents>,
    pub init:         fn(&Client) -> iced::Result,
}

impl Default for Client{
    fn default() -> Self {
        Self {
            update:       def_fns::update::default,
            view:         def_fns::view::default,
            subscribe:    def_fns::subscribe::default,
            init,
        }
    }
}
