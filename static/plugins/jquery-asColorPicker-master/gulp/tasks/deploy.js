'use strict';

import config from '../../config';
import gulp from 'gulp';
import inquirer from 'inquirer';
import replace from 'gulp-replace';
import { execSync as exec, spawnSync as spawn } from 'child_process';
import semver from 'semver';
import gutil from 'gulp-util';

const CURRENT_VERSION = config.version;
let NEXT_VERSION;
let NEXT_MESSAGE;

export function prompt(done) {
  inquirer.prompt([{
    type: 'input',
    name: 'version',
    message: `What version are we moving to? (Current version is ${CURRENT_VERSION})`,
    validate: function (input) {
      if(input === '') {
        input = CURRENT_VERSION;
      }
      return /^\d*[\d.]*\d*$/.test(input);
    }
  }]).then((answers) => {
    if (answers.version === '') {
      NEXT_VERSION = semver.inc(CURRENT_VERSION, config.deploy.increment);
      gutil.log(gutil.colors.green(`No version inputted, bump to version ${NEXT_VERSION}`));
    } else {
      NEXT_VERSION = answers.version;
    }

    done();
  });
}

export function message(done) {
  inquirer.prompt([{
    type: 'input',
    name: 'message',
    message: `What message are we going to commit?`,
    validate: function (input) {
      if(input === '' && NEXT_VERSION === CURRENT_VERSION) {
        return false;
      }
      return true;
    }
  }]).then((answers) => {
    if (answers.message !== '') {
      NEXT_MESSAGE = answers.message;
    } else {
      NEXT_MESSAGE = '';
    }
    done();
  });
}

// Bumps the version number in any file that has one
export function version() {
  return gulp.src(config.deploy.versionFiles, {
    base: process.cwd()
  })
    // .pipe(replace(CURRENT_VERSION, NEXT_VERSION))
    .pipe(replace(/Version\s*:\s*([\d.]+)/, `Version: ${NEXT_VERSION}`))
    .pipe(replace(/("|')version\1\s*:\s*("|')([\d.]+)\2/, `$1version$1: $2${NEXT_VERSION}$2`))
    .pipe(gulp.dest('.'));
}

export function init(done) {
  config.production = true;
  config.init();

  done();
}

// Writes a commit with the changes to the version numbers
export function commit(done) {
  let message = `Release ${NEXT_VERSION}`;

  if (NEXT_VERSION === CURRENT_VERSION) {
    message = NEXT_MESSAGE;
  } else if(NEXT_MESSAGE !== '') {
    message = `${message}; ${NEXT_MESSAGE}`;
  }
  exec('git add .');
  exec(`git commit -am "${message}"`);

  if (NEXT_VERSION !== CURRENT_VERSION) {
    exec(`git tag v${NEXT_VERSION}`);
  }

  exec('git push origin master --follow-tags');
  done();
}
