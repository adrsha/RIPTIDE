mod def_fns;
use std::path::Path;
use std::io::Result;


pub struct Writer {
    pub write  : fn(&[u8], &Path) -> Result<()>,
    pub append : fn(&[u8], &Path) -> Result<()>
}

impl Writer {
    pub fn default () -> Self {
        Writer  {
            write  : def_fns::init,
            append : def_fns::append
        }
    }
}
