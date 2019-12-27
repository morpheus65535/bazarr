'use strict';

import config from '../../config';
import gulp   from 'gulp';
import zip    from 'gulp-zip';
import notify from 'gulp-notify';

export default function (src = config.archive.src, dest = config.archive.dest, message = 'Archive task complete') {
  return function () {
    return gulp.src(src)
      .pipe(zip(`${config.version}.zip`))
      .pipe(gulp.dest(dest))
      .pipe(notify({
        title: config.notify.title,
        message: message
      }));
  };
}
