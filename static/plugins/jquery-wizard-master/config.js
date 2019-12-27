'use strict';

import fs from 'graceful-fs';
import minimist from 'minimist';

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
        entry: 'main.js',
        version: 'info.js',
        files: '**/*.js',
        src: `${src}`,
        dest: `${dest}`,
        prodSourcemap: false,
        test: './test',
        gulp: './gulp'
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

      notify: {
        title: pkg.title
      },

      test: {},
    };
  },

  init: function() {
    const pkg = JSON.parse(fs.readFileSync('./package.json', { encoding: 'utf-8' }));

    Object.assign(this, {
      args: minimist(process.argv.slice(2), {
        string: 'env',
        default: {
          env: process.env.NODE_ENV || 'dev'
        }
      })
    });

    if (this.args.env === 'dev') {
      this.dev = true;
    }

    if (typeof this.deploy === 'undefined') {
      this.deploy = false;
    }

    let src = 'src';
    let dest = 'dist';

    Object.assign(this, this.getConfig(pkg, src, dest));

    return this;
  }

}.init();
