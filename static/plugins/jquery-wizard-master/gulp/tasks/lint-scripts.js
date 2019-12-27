'use strict';

import config      from '../../config';
import gulp        from 'gulp';
import eslint      from 'gulp-eslint';
import jshint      from 'gulp-jshint';
import getSrcFiles from '../util/getSrcFiles';

export function es(src = config.scripts.src, options = {}, files = ['**/*.js', '!**/*.min.js']) {
  return function() {
    let srcFiles = getSrcFiles(src, files);

    options = Object.assign({
      useEslintrc: true,
      configFile: '.eslintrc.yml',
      fix: true
    }, options);

    return gulp.src(srcFiles)
      .pipe(eslint(options))
      .pipe(eslint.format())
      .pipe(eslint.failAfterError());
  };
}

export function js(src = config.scripts.src, files = ['**/*.js', '!**/*.min.js']) {
  return function() {
    let srcFiles = getSrcFiles(src, files);

    return gulp.src(srcFiles)
      .pipe(jshint({
        lookup: true
      }))
      .pipe(jshint.reporter('default'));
  };
}
