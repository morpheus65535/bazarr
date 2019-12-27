import $ from 'jquery';
import wizard from './wizard';
import info from './info';

const NAMESPACE = 'wizard';
const OtherWizard = $.fn.wizard;

const jQueryWizard = function(options, ...args) {
  if (typeof options === 'string') {
    const method = options;

    if (/^_/.test(method)) {
      return false;
    } else if ((/^(get)/.test(method))) {
      const instance = this.first().data(NAMESPACE);
      if (instance && typeof instance[method] === 'function') {
        return instance[method](...args);
      }
    } else {
      return this.each(function() {
        const instance = $.data(this, NAMESPACE);
        if (instance && typeof instance[method] === 'function') {
          instance[method](...args);
        }
      });
    }
  }

  return this.each(function() {
    if (!$(this).data(NAMESPACE)) {
      $(this).data(NAMESPACE, new wizard(this, options));
    }
  });
};

$.fn.wizard = jQueryWizard;

$.wizard = $.extend({
  setDefaults: wizard.setDefaults,
  noConflict: function() {
    $.fn.wizard = OtherWizard;
    return jQueryWizard;
  }
}, info);
