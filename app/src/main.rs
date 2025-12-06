use std::sync::{Arc, RwLock};
use riptide_lib::shared::frames::Frame;
use riptide_lib::{Libs, shared::RTShared };

#[tokio::main]
async fn main() {
    let shared_vars: Arc<RwLock<RTShared>> = Arc::new(RwLock::new(RTShared::default()));
    let libs: Libs = Libs::new(shared_vars);
    match libs.run_riptide() {
        Ok(_) => {}
        Err(err) => {
            print!("Error occured in run_riptide: {}", err);
        }
    }
}
