import $ from 'jquery';
import AsGradient from './asGradient';
import info from './info';
import GradientString from './gradientString';

const OtherAsGradient = $.asGradient;

const jQueryAsGradient = function(...args) {
  return new AsGradient(...args);
}

$.asGradient = jQueryAsGradient;
$.asGradient.Constructor = AsGradient;

$.extend($.asGradient, {
  setDefaults: AsGradient.setDefaults,
  noConflict: function() {
    $.asGradient = OtherAsGradient;
    return jQueryAsGradient;
  }
}, GradientString, info);

export default $.asGradient;
