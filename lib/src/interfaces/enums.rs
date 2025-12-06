#[derive(Debug, Clone)]
pub enum RiptideEvents {
    BufferEvents{ buffer_id: usize, actions: BufferActions },

    WindowCloseEvent{ window_id: u32 },
    WindowOpenEvent{ window_id: u32 },
    FrameCloseEvent{ window_id: usize, frame_id: usize },
    FrameOpenEvent{ window_id: usize, frame_id: usize },


    // system
    FileOpened{ path: String },
    FileSaved{ path: String },

    // LSP
    // LspDiagnostics(Vec<Diagnostic>),
    // LspCompletionRequest(String),
    //
    // // treesitter
    // SyntaxTreeUpdated,
    //
    // // undo-tree
    // Undo,
    // Redo,
}

#[derive(Debug, Clone)]
pub enum BufferActions {
    InsertText { text: String },
    DeleteRange { start: usize, end: usize },
    CursorMoved { line: usize, col: usize },
}
