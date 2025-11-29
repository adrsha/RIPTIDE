use crate::client::{Client };
use crate::interfaces::enums::ClientEvents;
use iced::{Task, window};

pub fn default(client : &mut Client, events: ClientEvents ) {
    match events {
        ClientEvents::Ignored => {}
        ClientEvents::KeyDown => {}
        ClientEvents::LeftMouseBtnDown => {},
        ClientEvents::RightMouseBtnDown => {},
        ClientEvents::WindowOpenEvent(id) => {
            println!("damn girl the window is wide open nowwww !!");
            // window::open(id);
        },
        ClientEvents::WindowCloseEvent(id) => {
            client.windows.retain(|win| win.id != Some(id));
            window::close(id) as Task<ClientEvents>;
        },
        ClientEvents::FrameCloseEvent(f_id, w_id) => {
            let frame_cluster_index = client.windows[w_id].frame_cluster_index;
            client.shared.frames.frame_clusters[frame_cluster_index].frames.remove(f_id);
        },
        ClientEvents::FrameOpenEvent(f_id, w_id) => {
            let frame_cluster_index = client.windows[w_id].frame_cluster_index;
            client.shared.frames.frame_clusters[frame_cluster_index].frames.push(f_id);
        },
    }
}

