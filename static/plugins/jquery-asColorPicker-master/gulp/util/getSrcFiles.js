'use strict';

import {argv} from 'yargs';
import path       from 'path';
import pathExists from 'path-exists';

export default function(src, files, argName = 'file') {
  let srcFiles = '';

  if(argv[argName] && pathExists.sync(path.join(src, argv[argName]))) {
    let arg = argv[argName];
    srcFiles = `${src}/${arg}`;
  } else if(Array.isArray(files)) {
    srcFiles = files.map((file) => {
      if(file.indexOf('!') === 0) {
        file = file.substr(1);
        return `!${src}/${file}`;
      }

      return `${src}/${file}`;
    });
  } else {
    srcFiles = `${src}/${files}`;
  }

  return srcFiles;
}
