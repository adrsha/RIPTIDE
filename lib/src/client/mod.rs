mod windows;
mod def_fns {
    pub mod run;
}
mod events;

use def_fns::run;
use windows::def_fns::window_mgmt;
use windows::RTWindow;


use eframe::egui::{self, ViewportId, X11WindowType};
use crate::{
    interfaces::enums::RiptideEvents, shared::{self, RTShared}
};
use tokio::sync::broadcast;
use std::sync::{Arc, RwLock};


pub struct RTClient {
    pub viewport_options       : egui::ViewportBuilder,
    pub next_frame_cluster_idx : usize,
    pub side_windows : Arc<RwLock<Vec<RTWindow>>>,
    pub shared  : Arc<RwLock<RTShared>>,

    pub load_side_windows   : fn(&mut Self),
    pub create_side_windows : fn(&mut Self, &egui::Context),
    pub create_main_window  : fn(&mut Self, &egui::Context),

    pub run_ui              : fn(RTClient) -> eframe::Result,
    pub events : events::RTEvents,

    is_alive: bool,
}


impl RTClient {
    pub fn new(shared: Arc<RwLock<shared::RTShared>>, bus : broadcast::Sender<RiptideEvents>) -> Self {
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
            side_windows : Arc::new( RwLock::new( vec![])),
            shared,

            load_side_windows   : window_mgmt::load_side_windows,
            create_main_window  : window_mgmt::create_main_window,
            create_side_windows : window_mgmt::create_side_windows,
            run_ui              : run::run_ui,

            events : events::RTEvents::default(),

            is_alive: false,
        }
    }

}


impl eframe::App for RTClient {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if !self.is_alive {
            (self.events.on_client_open)(self);
            (self.load_side_windows)(self);
            self.is_alive = true;
        }
        (self.create_main_window) (self, ctx);
        (self.create_side_windows)(self, ctx);
    }
}
