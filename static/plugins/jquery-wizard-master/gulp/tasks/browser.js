'use strict';

import config   from '../../config';
import browser  from 'browser-sync';
import notifier from 'node-notifier';

export function init(options = {}, message = 'Browser starting') {
  options = Object.assign(options, {
    server: {
      baseDir: config.browser.baseDir,
    },
    startPath: config.browser.startPath,
    port: config.browser.browserPort,
    ui: {
      port: config.browser.UIPort
    },
    ghostMode: {
      links: false
    }
  });

  return function() {
    browser.init(options, () => {
      notifier.notify({
        title: config.notify.title,
        message: message
      });
    });
  };
}

export function reload(message = 'Browser reloaded') {
  return function(done) {
    browser.reload();
    done();

    notifier.notify({
      title: config.notify.title,
      message: message
    });
  };
}
