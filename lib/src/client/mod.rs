mod def_fns {
    pub mod windows {
        pub mod window_mgmt;
        pub mod windows;
    }
    pub mod events;
}

use def_fns::events;
use def_fns::windows::window_mgmt;
use def_fns::windows::windows::RTWindow;

use eframe::egui::{self, ViewportId, X11WindowType};
use crate::shared::{self, RTShared};
use std::sync::{Arc, RwLock};


pub struct RTClient {
    pub viewport_options       : egui::ViewportBuilder,
    pub next_frame_cluster_idx : usize,
    pub windows : Arc<RwLock<Vec<RTWindow>>>,
    pub shared  : Arc<RwLock<RTShared>>,

    pub load_windows : fn(&mut Self),
    pub create_side_windows : fn(&mut Self, &egui::Context),
    pub create_main_window  : fn(&mut Self, &egui::Context),

    pub events : events::RTEvents,

    is_alive: bool,
}


impl RTClient {
    pub fn new(shared: Arc<RwLock<shared::RTShared>>) -> Self {
        Self {
            viewport_options: egui::ViewportBuilder::default()
                .with_title("Riptide")
                .with_active(true)
                .with_app_id("riptide")
                .with_resizable(true)
                .with_maximized(false)
                .with_taskbar(false)
                .with_close_button(false)
                .with_decorations(false)
                .with_window_type(X11WindowType::Normal)
                .with_transparent(false)
                .with_titlebar_buttons_shown(false)
                .with_has_shadow(true)
                .with_visible(true)
                .with_inner_size([320.0, 240.0]),
            next_frame_cluster_idx : 0,
            windows : Arc::new( RwLock::new( vec![RTWindow::default(String::from("Riptide Default"), 0)])),
            shared,

            load_windows        : window_mgmt::load_windows,
            create_main_window  : window_mgmt::create_main_window,
            create_side_windows : window_mgmt::create_side_windows,

            events : events::RTEvents::default(),

            is_alive: false,
        }
    }

}


impl eframe::App for RTClient {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if !self.is_alive {
            (self.events.on_client_open)(self);
            (self.load_windows)(self);
            self.is_alive = true;
        }
        (self.create_main_window) (self, ctx);
        (self.create_side_windows)(self, ctx);
    }
}
