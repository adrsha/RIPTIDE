use crate::client::{RTClient, RTWindow};

pub struct RTEvents {
    pub on_client_open  : fn(&mut RTClient) -> (),
    pub on_client_close : fn(&mut RTClient) -> (),
    pub on_window_open  : fn(&mut RTWindow) -> (),
    pub on_window_close : fn(&mut RTWindow) -> (),
}

impl Default for RTEvents {
    fn default() -> Self {
        Self {
            on_client_open : |_client: &mut RTClient| {},
            on_client_close: |_client: &mut RTClient| {},
            on_window_open : |_window: &mut RTWindow| {},
            on_window_close: |_window: &mut RTWindow| {} 
        }
    }
}
