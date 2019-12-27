module.exports = function(config) {
  'use strict';

  config.set({
    autoWatch: true,
    browsers:  ['Firefox'],

    files: [
      'vendor/*.js',
      'lib/*.css',
      'lib/*.js',
      'spec/lib/jasmine-jquery.js',
      'spec/lib/helper.js',
      'spec/options_spec.js',
      'spec/*spec.js'
    ],

    frameworks: ['jasmine'],
    logLevel:   config.LOG_ERROR,
    port:       9876,
    reporters:  ['dots'],
    singleRun:  true
  });
};
