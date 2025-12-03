use std::fs::File;
use std::path::Path;
use memmap2::{MmapOptions, Mmap};

pub fn read_file_chunk(path : &Path, offset : Option<u64>, length : Option<usize>) -> std::io::Result<Mmap> {
    let length = length.unwrap_or(0);
    let offset = offset.unwrap_or(4096);

    let file = File::open(path).unwrap();
    let mmap = unsafe {
        MmapOptions::new()
            .offset(offset)  // start mapping from byte 1024
            .len   (length)  // map 4KB
            .map   (&file).unwrap()
    };
    Ok(mmap)
}

pub fn read_entire_file(path : &Path) -> std::io::Result<Mmap> {

    let file = File::open(path).unwrap();
    let mmap = unsafe {
        MmapOptions::new()
            .map(&file).unwrap()
    };
    Ok(mmap)
}
