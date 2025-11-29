pub mod client;
pub mod server;
pub mod shared;
pub mod interfaces {
    pub mod enums;
}

pub struct Libs {
    pub client : client::Client,
}

impl Libs {
    pub fn default() -> Self {
        Self {
            client : client::Client::default(),
        }
    }
}


pub fn run_riptide(libs : Libs) {
    let client = libs.client;

    if let Err(e) = (client)(&client.windows) {
        println!("Error: {}", e);
    }
}
