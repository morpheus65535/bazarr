'use strict';

import config       from '../../config';
import gulp         from 'gulp';
import babel        from 'gulp-babel';
import gulpif       from 'gulp-if';
import sourcemaps   from 'gulp-sourcemaps';
import handleErrors from '../util/handleErrors';
import getSrcFiles  from '../util/getSrcFiles';
import browser      from 'browser-sync';
import header       from 'gulp-header';
import rename       from 'gulp-rename';
import rollup       from 'gulp-rollup';
import uglify       from 'gulp-uglify';
import size         from 'gulp-size';
import plumber      from 'gulp-plumber';
import prettier     from 'gulp-nf-prettier';
import path         from 'path';
import notify       from 'gulp-notify';
import replace      from 'gulp-replace';

export function bundler(src = config.scripts.src, dest = config.scripts.dest, input = config.scripts.input, files = config.scripts.files, message = 'Bundler task complete') {
  return function () {
    let srcFiles = getSrcFiles(src, files);

    return gulp.src(srcFiles)
      .on('error', handleErrors)
      .pipe(plumber({errorHandler: handleErrors}))
      .pipe(rollup({
        input: `${src}/${input}`,
        format: 'es',
        globals: {
          jquery: 'jQuery',
          "jquery-asColor": "AsColor",
          "jquery-asGradient": "AsGradient"
        }
      }))
      .pipe(header(config.banner))
      .pipe(rename({
        basename: config.name,
        suffix: '.es'
      }))
      .pipe(gulp.dest(dest))
      .pipe(notify({
        title: config.notify.title,
        message: message,
        onLast: true
      }));
  };
}

export function scripts(src = config.scripts.src, dest = config.scripts.dest, input = config.scripts.input, files = config.scripts.files, message = 'Scripts task complete') {
  const createSourcemap = config.deploy || config.scripts.prodSourcemap;

  return function () {
    let srcFiles = getSrcFiles(src, files);

    return gulp.src(`${dest}/${config.name}.es.js`)
      .on('error', handleErrors)
      .pipe(plumber({errorHandler: handleErrors}))
      // .pipe(rollup({
      //   input: `${src}/${input}`,
      // }))
      .pipe(babel({
        "presets": ["es2015"],
        "plugins": [
          ["transform-es2015-modules-umd", {
            "globals": {
              "jquery": "jQuery",
              "jquery-asColor": "AsColor",
              "jquery-asGradient": "AsGradient"
            }
          }]
        ]
      }))
      .pipe(header(config.banner))
      .pipe(
        prettier({
          parser: 'flow',
          tabWidth: 2,
          useTabs: false,
          semi: true,
          singleQuote: true,
          bracketSpacing: true,
        })
      )
      .pipe(rename({
        basename: config.name
      }))
      .pipe(gulp.dest(dest))
      .pipe(size({
        title: 'scripts',
        showFiles: true
      }))
      .pipe(rename({
        suffix: '.min'
      }))
      .pipe(gulpif(createSourcemap, sourcemaps.init()))
      .pipe(uglify())
      .pipe(header(config.banner))
      .pipe(gulpif(
        createSourcemap,
        sourcemaps.write(config.deploy ? './' : null))
      )
      .pipe(gulp.dest(dest))
      .pipe(size({
        title: 'minified scripts',
        showFiles: true
      }))
      .pipe(browser.stream())
      .pipe(notify({
        title: config.notify.title,
        message: message,
        onLast: true
      }));
  };
}

export function version(src = config.scripts.src, file = config.scripts.version) {
  return function() {
    return gulp.src(path.join(src, file), {base: "./"})
      .pipe(replace(/("{0,1}|'{0,1})version\1\s*:\s*("|')([\d.]+)\2/, `$1version$1:$2${config.version}$2`))
      .pipe(gulp.dest("./", {overwrite: true}));
  }
}
