use std::sync::{Arc, RwLock};
use riptide_lib::shared::frames::Frame;
use riptide_lib::{Libs, shared::RTShared };

#[tokio::main]
async fn main() {
    let shared_vars: Arc<RwLock<RTShared>> = Arc::new(RwLock::new(RTShared::default()));
    shared_vars.read().expect("Cannot find shared").frames.write().expect("Frames").frame_clusters[0].frames = vec![
        Frame::default(),
        Frame::default(),
    ];
    let libs: Libs = Libs::new(shared_vars);
    match libs.run_riptide() {
        Ok(_) => {}
        Err(err) => {
            print!("Error occured in run_riptide: {}", err);
        }
    }
}
