'use strict';

import config      from '../../config';
import gulp        from 'gulp';
import eslint      from 'gulp-eslint';
import getSrcFiles from '../util/getSrcFiles';

export function es(src = config.scripts.src, options = {}, files = ['**/*.js', '!**/*.min.js']) {
  return function() {
    let srcFiles = getSrcFiles(src, files);

    options = Object.assign({
      useEslintrc: true,
      configFile: '.eslintrc.json',
      fix: true
    }, options);

    return gulp.src(srcFiles, {
        base: './'
      })
      .pipe(eslint(options))
      .pipe(eslint.format())
      .pipe(eslint.failAfterError());
  };
}

