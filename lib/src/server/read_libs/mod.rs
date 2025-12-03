mod def_fns;
use std::path::Path;
use memmap2::Mmap;


pub struct Reader {
    pub chunk : fn(&Path, Option<u64>, Option<usize>) -> std::io::Result<Mmap>,
    pub file  : fn(&Path) -> std::io::Result<Mmap>
}

impl Reader {
    pub fn default () -> Self {
        Self {
            chunk : def_fns::read_file_chunk,
            file  : def_fns::read_entire_file
        }
    }
}
