- ok so mmap is useful for following scenarios:
    - mmap is tied to a file, so cant use same mmap for diff files
    - you open a file and keep it open, then open a mmap open and run a fxn passing mmap and file and content. to write contents to memory.
    ```
    let file = File::open(path)?;
    let mut mmap = unsafe { MmapMut::map_mut(&file)? };

    // Multiple writes to SAME file via same mmap
    write_chunk(&mut mmap, 0, &data1)?;
    write_chunk(&mut mmap, 100, &data2)?;
    write_chunk(&mut mmap, 200, &data3)?;
    ```
    - you have a massive file you open a mmap, open a file, pass them to a fxn, it writes to the file.
        - only for random access not at last or first
    - reading large files without modifynig
