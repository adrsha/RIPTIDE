use std::sync::{Arc, RwLock};
use riptide_lib::{Libs, run_riptide, shared::RTShared };

fn main() {
    let shared_vars: RTShared = Arc::new(RwLock::new(RTShared::default()));
    let libs: Libs = Libs::new(&shared_vars);
    match run_riptide(libs) {
        Ok(_) => {}
        Err(err) => {
            print!("Error occured in run_riptide: {}", err);
        }
    }
}
