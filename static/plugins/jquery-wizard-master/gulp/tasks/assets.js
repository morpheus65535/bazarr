'use strict';

import config        from '../../config';
import merge         from 'merge-stream';
import gulp          from 'gulp';this
import notify        from 'gulp-notify';
import AssetsManager from 'assets-manager';
import argv          from 'argv';

argv.option([
  {
    name: 'package',
    short: 'p',
    type: 'string'
  }
]);

function getPackage() {
  let args = argv.run();
  if(args.options.package){
    return args.options.package;
  }
  return null;
}

/*
 * Checkout https://github.com/amazingSurge/assets-manager
 */
export function copy(options = config.assets, message = 'Assets task complete') {
  return function (done) {
    let pkgName = getPackage();
    const manager = new AssetsManager('manifest.json', options);

    if(pkgName) {
      manager.copyPackage(pkgName).then(()=>{
        done();
      });
    } else {
      manager.copyPackages().then(()=>{
        done();
      });
    }
  }
}

export function clean(options = config.assets, message = 'Assets clean task complete') {
  return function (done) {
    let pkgName = getPackage();
    const manager = new AssetsManager('manifest.json', options);

    if(pkgName) {
      manager.cleanPackage(pkgName).then(()=>{
        done();
      });
    } else {
      manager.cleanPackages().then(()=>{
        done();
      });
    }
  }
}
