'use strict';

import config      from '../../config';
import gulp        from 'gulp';
import csslint     from 'gulp-csslint';
import scsslint    from 'gulp-scss-lint';
import stylelint   from 'gulp-stylelint';
import getSrcFiles from '../util/getSrcFiles';

export function css(src = config.styles.dest, files = ['**/*.css', '!**/*.min.css']) {
  return function() {
    let srcFiles = getSrcFiles(src, files);

    return gulp.src(srcFiles)
      .pipe(csslint('.csslintrc'))
      .pipe(csslint.reporter());
  };
}

export function scss(src = config.styles.src, files = '**/*.scss') {
  return function() {
    let srcFiles = getSrcFiles(src, files);

    return gulp.src(srcFiles)
      .pipe(scsslint({
        config: '.scss-lint.yml'
      }));
  };
}

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
