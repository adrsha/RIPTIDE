mod handle_shared;
use std::sync::{RwLock, Arc};

use crate::server::Writer;
use crate::shared::RTShared;

pub struct SharedHandler {
    pub save_shared : fn(writer : &Writer, shared : Arc<RwLock<RTShared>>),
}

impl SharedHandler {
    pub fn default () -> Self {
        SharedHandler  {
            save_shared : handle_shared::save_shared,
        }
    }
}
