use riptide_lib::{Libs, run_riptide };
// use crate::shared::frames::FrameStorage;
// use crate::shared::buffers::BufferStorage;

fn main() {
    let libs = Libs::default();
    // {
    //     let mut writable_shared = shared::SHARED.write().unwrap();
    //     writable_shared.frames = FrameStorage::default();
    //     writable_shared.buffers = BufferStorage::default();
    // }
    // let client = libs.client;
    // client.subscribe = new_func;
    run_riptide(libs);
}
