/**
* jQuery asGradient v0.3.3
* https://github.com/amazingSurge/jquery-asGradient
*
* Copyright (c) amazingSurge
* Released under the LGPL-3.0 license
*/
import $ from 'jquery';
import Color from 'jquery-asColor';

var DEFAULTS = {
  prefixes: ['-webkit-', '-moz-', '-ms-', '-o-'],
  forceStandard: true,
  angleUseKeyword: true,
  emptyString: '',
  degradationFormat: false,
  cleanPosition: true,
  color: {
    format: false, // rgb, rgba, hsl, hsla, hex
    hexUseName: false,
    reduceAlpha: true,
    shortenHex: true,
    zeroAlphaAsTransparent: false,
    invalidValue: {
      r: 0,
      g: 0,
      b: 0,
      a: 1
    }
  }
};

/* eslint no-extend-native: "off" */
if (!String.prototype.includes) {
  String.prototype.includes = function(search, start) {
    'use strict';
    if (typeof start !== 'number') {
      start = 0;
    }

    if (start + search.length > this.length) {
      return false;
    }
    return this.indexOf(search, start) !== -1;
  };
}

function getPrefix() {
  const ua = window.navigator.userAgent;
  let prefix = '';
  if (/MSIE/g.test(ua)) {
    prefix = '-ms-';
  } else if (/Firefox/g.test(ua)) {
    prefix = '-moz-';
  } else if (/(WebKit)/i.test(ua)) {
    prefix = '-webkit-';
  } else if (/Opera/g.test(ua)) {
    prefix = '-o-';
  }
  return prefix;
}

function flip(o) {
  const flipped = {};
  for (const i in o) {
    if (o.hasOwnProperty(i)) {
      flipped[o[i]] = i;
    }
  }
  return flipped;
}

function reverseDirection(direction) {
  const mapping = {
    'top': 'bottom',
    'right': 'left',
    'bottom': 'top',
    'left': 'right',
    'right top': 'left bottom',
    'top right': 'bottom left',
    'bottom right': 'top left',
    'right bottom': 'left top',
    'left bottom': 'right top',
    'bottom left': 'top right',
    'top left': 'bottom right',
    'left top': 'right bottom'
  };
  return mapping.hasOwnProperty(direction) ? mapping[direction] : direction;
}

function isDirection(n) {
  const reg = /^(top|left|right|bottom)$/i;
  return reg.test(n);
}

var keywordAngleMap = {
  'to top': 0,
  'to right': 90,
  'to bottom': 180,
  'to left': 270,
  'to right top': 45,
  'to top right': 45,
  'to bottom right': 135,
  'to right bottom': 135,
  'to left bottom': 225,
  'to bottom left': 225,
  'to top left': 315,
  'to left top': 315
};

const angleKeywordMap = flip(keywordAngleMap);

const RegExpStrings = (() => {
  const color = /(?:rgba|rgb|hsla|hsl)\s*\([\s\d\.,%]+\)|#[a-z0-9]{3,6}|[a-z]+/i;
  const position = /\d{1,3}%/i;
  const angle = /(?:to ){0,1}(?:(?:top|left|right|bottom)\s*){1,2}|\d+deg/i;
  const stop = new RegExp(`(${color.source})\\s*(${position.source}){0,1}`, 'i');
  const stops = new RegExp(stop.source, 'gi');
  const parameters = new RegExp(`(?:(${angle.source})){0,1}\\s*,{0,1}\\s*(.*?)\\s*`, 'i');
  const full = new RegExp(`^(-webkit-|-moz-|-ms-|-o-){0,1}(linear|radial|repeating-linear)-gradient\\s*\\(\\s*(${parameters.source})\\s*\\)$`, 'i');

  return {
    FULL: full,
    ANGLE: angle,
    COLOR: color,
    POSITION: position,
    STOP: stop,
    STOPS: stops,
    PARAMETERS: new RegExp(`^${parameters.source}$`, 'i')
  };
})();

var GradientString = {
  matchString: function(string) {
    const matched = this.parseString(string);
    if(matched && matched.value && matched.value.stops && matched.value.stops.length > 1){
      return true;
    }
    return false;
  },

  parseString: function(string) {
    string = $.trim(string);
    let matched;
    if ((matched = RegExpStrings.FULL.exec(string)) !== null) {
      let value = this.parseParameters(matched[3]);

      return {
        prefix: (typeof matched[1] === 'undefined') ? null : matched[1],
        type: matched[2],
        value: value
      };
    } else {
      return false;
    }
  },

  parseParameters: function(string) {
    let matched;
    if ((matched = RegExpStrings.PARAMETERS.exec(string)) !== null) {
      let stops = this.parseStops(matched[2]);
      return {
        angle: (typeof matched[1] === 'undefined') ? 0 : matched[1],
        stops: stops
      };
    } else {
      return false;
    }
  },

  parseStops: function(string) {
    let matched;
    const result = [];
    if ((matched = string.match(RegExpStrings.STOPS)) !== null) {

      $.each(matched, (i, item) => {
        const stop = this.parseStop(item);
        if (stop) {
          result.push(stop);
        }
      });
      return result;
    } else {
      return false;
    }
  },

  formatStops: function(stops, cleanPosition) {
    let stop;
    const output = [];
    let positions = [];
    const colors = [];
    let position;

    for (let i = 0; i < stops.length; i++) {
      stop = stops[i];
      if (typeof stop.position === 'undefined' || stop.position === null) {
        if (i === 0) {
          position = 0;
        } else if (i === stops.length - 1) {
          position = 1;
        } else {
          position = undefined;
        }
      } else {
        position = stop.position;
      }
      positions.push(position);
      colors.push(stop.color.toString());
    }

    positions = ((data => {
      let start = null;
      let average;
      for (let i = 0; i < data.length; i++) {
        if (isNaN(data[i])) {
          if (start === null) {
            start = i;
            continue;
          }
        } else if (start) {
          average = (data[i] - data[start - 1]) / (i - start + 1);
          for (let j = start; j < i; j++) {
            data[j] = data[start - 1] + (j - start + 1) * average;
          }
          start = null;
        }
      }

      return data;
    }))(positions);

    for (let x = 0; x < stops.length; x++) {
      if (cleanPosition && ((x === 0 && positions[x] === 0) || (x === stops.length - 1 && positions[x] === 1))) {
        position = '';
      } else {
        position = ` ${this.formatPosition(positions[x])}`;
      }

      output.push(colors[x] + position);
    }
    return output.join(', ');
  },

  parseStop: function(string) {
    let matched;
    if ((matched = RegExpStrings.STOP.exec(string)) !== null) {
      let position = this.parsePosition(matched[2]);

      return {
        color: matched[1],
        position: position
      };
    } else {
      return false;
    }
  },

  parsePosition: function(string) {
    if (typeof string === 'string' && string.substr(-1) === '%') {
      string = parseFloat(string.slice(0, -1) / 100);
    }

    if(typeof string !== 'undefined' && string !== null) {
      return parseFloat(string, 10);
    } else {
      return null;
    }
  },

  formatPosition: function(value) {
    return `${parseInt(value * 100, 10)}%`;
  },

  parseAngle: function(string, notStandard) {
    if (typeof string === 'string' && string.includes('deg')) {
      string = string.replace('deg', '');
    }
    if (!isNaN(string)) {
      if (notStandard) {
        string = this.fixOldAngle(string);
      }
    }
    if (typeof string === 'string') {
      const directions = string.split(' ');

      const filtered = [];
      for (const i in directions) {
        if (isDirection(directions[i])) {
          filtered.push(directions[i].toLowerCase());
        }
      }
      let keyword = filtered.join(' ');

      if (!string.includes('to ')) {
        keyword = reverseDirection(keyword);
      }
      keyword = `to ${keyword}`;
      if (keywordAngleMap.hasOwnProperty(keyword)) {
        string = keywordAngleMap[keyword];
      }
    }
    let value = parseFloat(string, 10);

    if (value > 360) {
      value %= 360;
    } else if (value < 0) {
      value %= -360;

      if (value !== 0) {
        value += 360;
      }
    }
    return value;
  },

  fixOldAngle: function(value) {
    value = parseFloat(value);
    value = Math.abs(450 - value) % 360;
    value = parseFloat(value.toFixed(3));
    return value;
  },

  formatAngle: function(value, notStandard, useKeyword) {
    value = parseInt(value, 10);
    if (useKeyword && angleKeywordMap.hasOwnProperty(value)) {
      value = angleKeywordMap[value];
      if (notStandard) {
        value = reverseDirection(value.substr(3));
      }
    } else {
      if (notStandard) {
        value = this.fixOldAngle(value);
      }
      value = `${value}deg`;
    }

    return value;
  }
};

class ColorStop {
  constructor(color, position, gradient) {
    this.color = Color(color, gradient.options.color);
    this.position = GradientString.parsePosition(position);
    this.id = ++gradient._stopIdCount;
    this.gradient = gradient;
  }

  setPosition(string) {
    const position = GradientString.parsePosition(string);
    if(this.position !== position){
      this.position = position;
      this.gradient.reorder();
    }
  }

  setColor(string) {
    this.color.fromString(string);
  }

  remove() {
    this.gradient.removeById(this.id);
  }
}

var GradientTypes = {
  LINEAR: {
    parse(result) {
      return {
        r: (result[1].substr(-1) === '%') ? parseInt(result[1].slice(0, -1) * 2.55, 10) : parseInt(result[1], 10),
        g: (result[2].substr(-1) === '%') ? parseInt(result[2].slice(0, -1) * 2.55, 10) : parseInt(result[2], 10),
        b: (result[3].substr(-1) === '%') ? parseInt(result[3].slice(0, -1) * 2.55, 10) : parseInt(result[3], 10),
        a: 1
      };
    },
    to(gradient, instance, prefix) {
      if (gradient.stops.length === 0) {
        return instance.options.emptyString;
      }
      if (gradient.stops.length === 1) {
        return gradient.stops[0].color.to(instance.options.degradationFormat);
      }

      let standard = instance.options.forceStandard;
      let _prefix = instance._prefix;

      if (!_prefix) {
        standard = true;
      }
      if (prefix && -1 !== $.inArray(prefix, instance.options.prefixes)) {
        standard = false;
        _prefix = prefix;
      }

      const angle = GradientString.formatAngle(gradient.angle, !standard, instance.options.angleUseKeyword);
      const stops = GradientString.formatStops(gradient.stops, instance.options.cleanPosition);

      const output = `linear-gradient(${angle}, ${stops})`;
      if (standard) {
        return output;
      } else {
        return _prefix + output;
      }
    }
  }
};

class AsGradient {
  constructor(string, options) {
    if (typeof string === 'object' && typeof options === 'undefined') {
      options = string;
      string = undefined;
    }
    this.value = {
      angle: 0,
      stops: []
    };
    this.options = $.extend(true, {}, DEFAULTS, options);

    this._type = 'LINEAR';
    this._prefix = null;
    this.length = this.value.stops.length;
    this.current = 0;
    this._stopIdCount = 0;

    this.init(string);
  }

  init(string) {
    if (string) {
      this.fromString(string);
    }
  }

  val(value) {
    if (typeof value === 'undefined') {
      return this.toString();
    } else {
      this.fromString(value);
      return this;
    }
  }

  angle(value) {
    if (typeof value === 'undefined') {
      return this.value.angle;
    } else {
      this.value.angle = GradientString.parseAngle(value);
      return this;
    }
  }

  append(color, position) {
    return this.insert(color, position, this.length);
  }

  reorder() {
    if(this.length < 2){
      return;
    }

    this.value.stops = this.value.stops.sort((a, b) => a.position - b.position);
  }

  insert(color, position, index) {
    if (typeof index === 'undefined') {
      index = this.current;
    }

    const stop = new ColorStop(color, position, this);

    this.value.stops.splice(index, 0, stop);

    this.length = this.length + 1;
    this.current = index;
    return stop;
  }

  getById(id) {
    if(this.length > 0){
      for(const i in this.value.stops){
        if(id === this.value.stops[i].id){
          return this.value.stops[i];
        }
      }
    }
    return false;
  }

  removeById(id) {
    const index = this.getIndexById(id);
    if(index){
      this.remove(index);
    }
  }

  getIndexById(id) {
    let index = 0;
    for(const i in this.value.stops){
      if(id === this.value.stops[i].id){
        return index;
      }
      index ++;
    }
    return false;
  }

  getCurrent() {
    return this.value.stops[this.current];
  }

  setCurrentById(id) {
    let index = 0;
    for(const i in this.value.stops){
      if(this.value.stops[i].id !== id){
        index ++;
      } else {
        this.current = index;
      }
    }
  }

  get(index) {
    if (typeof index === 'undefined') {
      index = this.current;
    }
    if (index >= 0 && index < this.length) {
      this.current = index;
      return this.value.stops[index];
    } else {
      return false;
    }
  }

  remove(index) {
    if (typeof index === 'undefined') {
      index = this.current;
    }
    if (index >= 0 && index < this.length) {
      this.value.stops.splice(index, 1);
      this.length = this.length - 1;
      this.current = index - 1;
    }
  }

  empty() {
    this.value.stops = [];
    this.length = 0;
    this.current = 0;
  }

  reset() {
    this.value._angle = 0;
    this.empty();
    this._prefix = null;
    this._type = 'LINEAR';
  }

  type(type) {
    if (typeof type === 'string' && (type = type.toUpperCase()) && typeof GradientTypes[type] !== 'undefined') {
      this._type = type;
      return this;
    } else {
      return this._type;
    }
  }

  fromString(string) {
    this.reset();

    const result = GradientString.parseString(string);

    if (result) {
      this._prefix = result.prefix;
      this.type(result.type);
      if (result.value) {
        this.value.angle = GradientString.parseAngle(result.value.angle, this._prefix !== null);

        $.each(result.value.stops, (i, stop) => {
          this.append(stop.color, stop.position);
        });
      }
    }
  }

  toString(prefix) {
    if(prefix === true){
      prefix = getPrefix();
    }
    return GradientTypes[this.type()].to(this.value, this, prefix);
  }

  matchString(string) {
    return GradientString.matchString(string);
  }

  toStringWithAngle(angle, prefix) {
    const value = $.extend(true, {}, this.value);
    value.angle = GradientString.parseAngle(angle);

    if(prefix === true){
      prefix = getPrefix();
    }

    return GradientTypes[this.type()].to(value, this, prefix);
  }

  getPrefixedStrings() {
    const strings = [];
    for (let i in this.options.prefixes) {
      if(Object.hasOwnProperty.call(this.options.prefixes, i)){
        strings.push(this.toString(this.options.prefixes[i]));
      }
    }
    return strings;
  }

  static setDefaults(options) {
    $.extend(true, DEFAULTS, $.isPlainObject(options) && options);
  }
}

var info = {
  version:'0.3.3'
};

const OtherAsGradient = $.asGradient;

const jQueryAsGradient = function(...args) {
  return new AsGradient(...args);
};

$.asGradient = jQueryAsGradient;
$.asGradient.Constructor = AsGradient;

$.extend($.asGradient, {
  setDefaults: AsGradient.setDefaults,
  noConflict: function() {
    $.asGradient = OtherAsGradient;
    return jQueryAsGradient;
  }
}, GradientString, info);

var main = $.asGradient;

export default main;
