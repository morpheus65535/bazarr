'use strict';

import config from '../../config';
import gulp   from 'gulp';
import path   from 'path';
import notify from 'gulp-notify';

export default function (src = config.images.src, dest = config.images.dest, files = config.images.files, message = 'Images task complete') {
  return function () {
    return gulp.src(path.join(src, files))
      .pipe(gulp.dest(dest))
      .pipe(notify({
        title: config.notify.title,
        message: message,
        onLast: true
      }));
  };
}
