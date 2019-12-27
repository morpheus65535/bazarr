'use strict';

import config from '../../config';
import del    from 'del';

export default function (src = config.paths.destDir) {
  return function (done) {
    del.sync([src]);

    done();
  };
}
