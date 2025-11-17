use crate::shared::frames::FrameCluster;
use crate::shared::Shared;
use crate::{client::{ ClientEvents, Client }, shared};
use iced::widget::{row, text };
use iced::{Element};

pub fn view_fn(client : &Client ) -> Element<ClientEvents> {
    let mut shared = shared::SHARED.write().unwrap();
    let mut container = row![];

    let frame_clusters = &mut shared.frames.frame_clusters;
    let main_frame_cluster;
    if let Some(frame_cluster) = frame_clusters.iter_mut().find(|fc| fc.is_visible) {
        main_frame_cluster = frame_cluster;
    } else {
        main_frame_cluster = frame_clusters.iter_mut().next().unwrap();
        main_frame_cluster.is_visible = true;
    }

    let current_frames = &main_frame_cluster.frames;
    for frame in current_frames {
        container = container.push(text(format!("Frame {}", frame.buffer_index)));
    }
    container.into()
}

pub use view_fn as default;
