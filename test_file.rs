use eframe::egui::{self, Context, Window};

#[derive(Default)]
struct DeferredWindow {
    id: u64,
    title: String,
    open: bool,
    shared: Shared,
}

impl DeferredWindow {
    fn show(&mut self, ctx: &Context) {
        if !self.open { return; }

        Window::new(&self.title)
            .open(&mut self.open)
            .show(ctx, |ui| {
                ui.label(format!("self.shared ... Documents: hell"));

                if ui.button("Add Document").clicked() { }
            });
    }
}

struct MyApp {
    windows: Vec<DeferredWindow>,
}

impl Default for MyApp {
    fn default() -> Self {
        Self {
            windows : vec![DeferredWindow::default()],
        }
    }
}
impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // show all windows independently
        for win in &mut self.windows {
            win.show(ctx);
        }

        // button to spawn a new window
        egui::CentralPanel::default().show(ctx, |ui| {
            if ui.button("New Window").clicked() {
                let id = rand::random();
                self.windows.push(DeferredWindow {
                    id,
                    title: format!("Window {}", id),
                    open: true,
                });
            }
        });
    }
}

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions::default();
    eframe::run_native(
            "egui Demo",
            options,
            Box::new(|_cc| Ok(Box::new(MyApp::default()))),
        )
}
