'use strict';

import fs from 'graceful-fs';
import {argv} from 'yargs';

const production = argv.production || argv.prod || false;

export default {
  getConfig: function(pkg, src, dest) {
    return {
      version: pkg.version,
      name: pkg.name,
      title: pkg.title,
      description: pkg.description,
      author: pkg.author,
      banner: `/**
* ${pkg.title} v${pkg.version}
* ${pkg.homepage}
*
* Copyright (c) ${pkg.author.name}
* Released under the ${pkg.license} license
*/
`,
      // basic locations
      paths: {
        root: './',
        srcDir: `${src}/`,
        destDir: `${dest}/`,
      },

      styles: {
        files: '**/*.scss',
        src: `${src}/scss`,
        dest: `${dest}/css`,
        prodSourcemap: false,
        sassIncludePaths: [],
        autoprefixer: {
          browsers: ['last 2 versions', 'ie >= 9', 'Android >= 2.3']
        }
      },

      scripts: {
        input: 'main.js',
        version: 'info.js',
        files: '**/*.js',
        src: `${src}`,
        dest: `${dest}`,
        prodSourcemap: false,
        test: './test',
        gulp: './gulp'
      },

      images: {
        files: '**/*.{png,jpg,gif,svg}',
        src: `${src}/images`,
        dest: `${dest}/images`
      },

      archive: {
        src: `${dest}/**/*`,
        dest: './archives/',
        zip: {}
      },

      browser: {
        baseDir: './',
        startPath: "examples/index.html",
        browserPort: 3000,
        UIPort: 3001,
        testPort: 3002,
      },

      deploy: {
        versionFiles: ['package.json', 'bower.json'],
        increment: "patch", // major, minor, patch, premajor, preminor, prepatch, or prerelease.
      },

      notify: {
        title: pkg.title
      },
      
      env: 'development',
      production: production,
      setEnv: function(env) {
        if (typeof env !== 'string') return;
        this.env = env;
        this.production = env === 'production';
        process.env.NODE_ENV = env;
      },

      test: {},
    };
  },

  init: function() {
    const pkg = JSON.parse(fs.readFileSync('./package.json', { encoding: 'utf-8' }));

    let src = 'src';
    let dest = 'dist';

    Object.assign(this, this.getConfig(pkg, src, dest, production));
    this.setEnv(production? 'production': 'development');

    return this;
  }

}.init();
