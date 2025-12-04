use crate::client::RTWindow;
use crate::client::RTClient;


pub struct RTEvents {
    pub on_client_open : fn(&mut RTClient) -> (),
}

impl RTEvents {
    pub fn on_client_open(client: &mut RTClient){
    }
}
