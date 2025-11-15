use std::sync::{LazyLock, RwLock};


pub mod client;
pub mod server;
pub mod shared;

pub struct Libs<'l>{
    gui : client::GUI,
    shared : &'l LazyLock<RwLock<shared::Shared>>,
}

impl<'l> Libs<'l> {
    pub fn default() -> Self {
        Self {
            gui : client::GUI::default(),
            shared : &shared::SHARED
        }
    }
}

pub enum RiptideEvents {
    OpenWindow
}

pub fn run_riptide(libs : Libs) {
    let gui = libs.gui;

    if let Err(e) = (gui.init)(gui.update, gui.view, gui.subscribe) {
        println!("Error: {}", e);
    }
}
