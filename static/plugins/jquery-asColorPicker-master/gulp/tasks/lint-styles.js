'use strict';

import config      from '../../config';
import gulp        from 'gulp';
import stylelint   from 'gulp-stylelint';
import getSrcFiles from '../util/getSrcFiles';

export function style(src = config.styles.src, files = '**/*.scss') {
  return function() {
    let srcFiles = getSrcFiles(src, files);

    return gulp.src(srcFiles)
      .pipe(stylelint({
        reporters: [{
          formatter: 'string',
          console: true
        }]
      }));
  };
}
