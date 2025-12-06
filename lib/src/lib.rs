pub mod client;
pub mod server;
pub mod shared;
pub mod interfaces {
    pub mod enums;
}

use tokio::sync::broadcast;
use std::sync::{Arc, RwLock};

use crate::interfaces::enums;

pub struct Libs {
    pub bus    : broadcast::Sender<enums::RiptideEvents>,
    pub client : client::RTClient,
    pub server : server::RTServer
}

// | Use case                                               | Best mechanism |
// | ------------------------------------------------------ | -------------- |
// | “User typed X” → rope, treesitter, LSP should all know | **broadcast**  |
// | “Get completions from LSP” → one reply needed          | **mpsc**       |
// | “Apply edit to buffer” → update rope only              | **mpsc**       |
// | “Redraw UI now”                                        | **broadcast**  |

impl Libs {
    pub fn new(shared: Arc<RwLock<shared::RTShared>>) -> Self {
        let (bus_tx, _) = broadcast::channel::<enums::RiptideEvents>(1024);

        let client = client::RTClient::new(shared.clone(), bus_tx.clone());
        let server = server::RTServer::new(shared.clone(), bus_tx.clone());

        Self { bus: bus_tx, client, server }
    }
    pub fn run_riptide(self) -> eframe::Result {
        (self.client.run_ui)(self.client)
    }
}


