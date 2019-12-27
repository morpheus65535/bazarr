'use strict';

import fs    from 'graceful-fs';
import path  from 'path';

export default function(dir) {
  return fs.readdirSync(dir).filter((file) => {
    return fs.statSync(path.join(dir, file)).isDirectory();
  });
}
