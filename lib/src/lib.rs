pub mod client;
pub mod server;
pub mod shared;

pub struct Libs{
    pub client : client::Client,
}

impl Libs {
    pub fn default() -> Self {
        Self {
            client : client::Client::default(),
        }
    }
}


pub enum RiptideEvents {
    OpenWindow
}

pub fn run_riptide(libs : Libs) {
    let client = libs.client;

    if let Err(e) = (client.init)(&client) {
        println!("Error: {}", e);
    }
}
