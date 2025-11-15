use iced::{application, Element, Subscription};

pub mod def_fns{
    pub mod view;
    pub mod update;
    pub mod subscribe;
}

#[derive(Debug)]
pub enum GUIEvents {
    KeyDown,
    LeftMouseBtnDown,
    RightMouseBtnDown,
    Ignored
}

fn init (
    update:    fn(&mut GUI, GUIEvents),
    view:      fn(&GUI) -> Element<GUIEvents>,
    subscribe: fn(&GUI) -> Subscription<GUIEvents>
) -> iced::Result {
    let application
        = application("RIPTIDE", update, view);
    application.subscription(subscribe).run()
}

pub struct GUI {
    pub update:       fn(&mut GUI, GUIEvents),
    pub view:         fn(&GUI) -> Element<GUIEvents>,
    pub subscribe:    fn(&GUI) -> Subscription<GUIEvents>,
    pub init:         fn(fn(&mut GUI, GUIEvents), fn(&GUI) -> Element<GUIEvents>, fn(&GUI) -> Subscription<GUIEvents>) -> iced::Result,
}

impl Default for GUI{
    fn default() -> Self {
        Self {
            update:       def_fns::update::default,
            view:         def_fns::view::default,
            subscribe:    def_fns::subscribe::default,
            init,
        }
    }
}
