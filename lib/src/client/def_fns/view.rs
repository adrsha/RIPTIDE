use crate::interfaces::enums::ClientEvents;
use crate::shared::frames::FrameCluster;
use crate::{client::Client};
use iced::widget::{row, text};
use iced::{Element};

fn check_new_frame_cluster(frame_clusters: &Vec<FrameCluster>) -> Option<&FrameCluster> {
    let mut new_frame_cluster = None;
    for frame_cluster in frame_clusters {
        if !frame_cluster.is_visible {
            new_frame_cluster = Some(frame_cluster);
            break;
        }
    }
    new_frame_cluster
}

pub fn default(client : &Client) -> Element<ClientEvents> {
    let mut container = row![];

    let frame_clusters = &client.shared.frames.frame_clusters;
    // TODO: check if current window has a pointed frame_cluster

    let new_frame_cluster = check_new_frame_cluster(&frame_clusters);

    match new_frame_cluster {
        Some(frame_cluster) => {
            for frame in frame_cluster.frames.iter() {
                container = container.push(text(format!("Frame {}", frame.buffer_index)));
            }
        },
        None => {
            container = container.push(text("No framesclusters found"));
        }
    }
    container.into()
}
