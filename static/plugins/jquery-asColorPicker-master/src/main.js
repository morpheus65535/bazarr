import $ from 'jquery';
import AsColorPicker from './asColorPicker';
import "./i18n/cn";
import "./i18n/de";
import "./i18n/dk";
import "./i18n/es";
import "./i18n/fi";
import "./i18n/fr";
import "./i18n/it";
import "./i18n/ja";
import "./i18n/ru";
import "./i18n/sv";
import "./i18n/tr";

import info from './info';

const NAMESPACE = 'asColorPicker';
const OtherAsColorPicker = $.fn.asColorPicker;

const jQueryAsColorPicker = function(options, ...args) {
  if (typeof options === 'string') {
    const method = options;

    if (/^_/.test(method)) {
      return false;
    } else if ((/^(get)$/.test(method)) || (method === 'val' && args.length === 0)) {
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
      $(this).data(NAMESPACE, new AsColorPicker(this, options));
    }
  });
};

$.fn.asColorPicker = jQueryAsColorPicker;

$.asColorPicker = $.extend({
  setDefaults: AsColorPicker.setDefaults,
  registerComponent: AsColorPicker.registerComponent,
  setLocalization: AsColorPicker.setLocalization,
  noConflict: function() {
    $.fn.asColorPicker = OtherAsColorPicker;
    return jQueryAsColorPicker;
  }
}, info);


