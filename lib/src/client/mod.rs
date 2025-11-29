use crate::interfaces::enums::ClientEvents;
use crate::shared::Shared;
use iced::{
    application, window, window::Id, Application, Task, Element, Settings,
    Subscription,
};

pub mod def_fns {
    pub mod view;
    pub mod update;
    pub mod subscribe;
}

fn spawn_window (
    current_window: &mut Window,
) -> Task<ClientEvents> {
    // let (id, spawn_task) = window::open(window::Settings {
    //     size:       iced::Size::new(800.0, 600.0),
    //     position:   window::Position::Default,
    //     visible:    true,
    //     resizable:  true,
    //     decorations: true,
    //     ..Default::default()
    // });
    // current_window.id = Some(id);
    // spawn_task.map(|id| ClientEvents::WindowOpenEvent(id))
}

pub fn spawn_client(windows: &mut Vec<Window>) -> iced::Result {

    // let mut tasks = Vec::new();
    //
    // for mut window in windows {
    //     let task = (window.spawn)(&mut window);
    //     tasks.push(task);
    // }
    //
    // let client = Client {
    //     windows:   windows,
    //     shared:    Shared::default(),
    //     update:    def_fns::update::default,
    //     view:      def_fns::view::default,
    //     subscribe: def_fns::subscribe::default,
    // };
    //
    // let application
    //     = application("RIPTIDE", client.update, client.view)
    //         .subscription(client.subscribe)
    //         .run_with(|| (client, Task::batch(tasks)));
    Ok(())
}

pub struct Client {
    pub windows:   Vec<Window>,
    pub shared :   Shared,
    pub update:    fn(&mut Self, ClientEvents),
    pub view:      fn(&Self) -> Element<ClientEvents>,
    pub subscribe: fn(&Self) -> Subscription<ClientEvents>,
}

impl Client {
    pub fn default() -> Self {
        Self {
            windows: vec![
                Window::default("Window"),
            ],
            shared: Shared::default(),
            update:    def_fns::update::default,
            view:      def_fns::view::default,
            subscribe: def_fns::subscribe::default,
        }
    }
}

#[derive(Clone)]
pub struct Window {
    pub id: Option<Id>,
    pub title: &'static str,
    pub frame_cluster_index : usize,
    pub spawn: fn(&mut Self) -> Task<ClientEvents>,
}

impl Window {
    pub fn default(
        title: &'static str,
    ) -> Self {
        Self {
            id: None,
            title,
            frame_cluster_index: 0,
            spawn: spawn_window,
        }
    }
}
