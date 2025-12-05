use memmap2::{MmapMut, MmapOptions};
use std::fs;
use std::path::Path;
use std::io::{Result, Seek, SeekFrom, Write};

fn handle_mem_write (
    original_size : Option<u64>,
    content : &[u8],
    file : &mut fs::File,
    is_big : bool
) -> Result<()> {

    let original_size = original_size.unwrap_or(0) as u64;
    let content_size  = content.len() as u64;
    let new_size      = original_size + content_size;

    file.set_len(new_size)?;
    match is_big {
        true => {
            let mut mmap : MmapMut = unsafe {
                MmapOptions::new().map_mut(&*file)?
            };

            let start = original_size as usize;
            let end   = start + content_size as usize;
            mmap[start..end].copy_from_slice(content);
            mmap.flush()?;

            Ok(())
        },
        false => {
            file.seek(SeekFrom::Start(original_size)).unwrap();
            file.write_all(content)?;
            file.flush()?;
            Ok(())
        }
    }
}

// overwrite a file
pub fn init(
    content : &[u8],
    path : &Path,
    is_big : bool
) -> Result<()> {
    let mut file = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(true) // reset the file
        .open(path)?;

    let original_file_size = None;

    handle_mem_write(original_file_size, content, &mut file, is_big)
}

// append new content to file
pub fn append(
    content : &[u8],
    path : &Path,
    is_big : bool
) -> Result<()> {

    let mut file = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(path)?;

    let original_file_size = Some(file.metadata()?.len());

    handle_mem_write(original_file_size, content, &mut file, is_big)
}
