'use strict';

import gutil       from 'gulp-util';
import esformatter from 'esformatter';
import through     from 'through2';
import fs          from 'graceful-fs';

export default function(options){
  return through.obj(function (file, enc, cb) {
    if (file.isNull()) {
      cb(null, file);
      return;
    }

    if (file.isStream()) {
      cb(new gutil.PluginError('esformatter', 'Streaming not supported'));
      return;
    }

    if (options.config) {
      options = JSON.parse(fs.readFileSync(options.config));
    }

    try {
      file.contents = new Buffer(esformatter.format(file.contents.toString(), esformatter.rc(file.path, options)));
      this.push(file);
    } catch (err) {
      this.emit('error', new gutil.PluginError('gulp-esformatter', err, {fileName: file.path}));
    }

    cb();
  });
}
