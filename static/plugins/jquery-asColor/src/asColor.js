import $ from 'jquery';
import DEFAULTS from './defaults';
import ColorStrings from './colorStrings';
import Converter from './converter';

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

class AsColor {
  constructor(string, options) {
    if (typeof string === 'object' && typeof options === 'undefined') {
      options = string;
      string = undefined;
    }
    if(typeof options === 'string'){
      options = {
        format: options
      };
    }
    this.options = $.extend(true, {}, DEFAULTS, options);
    this.value = {
      r: 0,
      g: 0,
      b: 0,
      h: 0,
      s: 0,
      v: 0,
      a: 1
    };
    this._format = false;
    this._matchFormat = 'HEX';
    this._valid = true;

    this.init(string);
  }

  init(string) {
    this.format(this.options.format);
    this.fromString(string);
    return this;
  }

  isValid() {
    return this._valid;
  }

  val(value) {
    if (typeof value === 'undefined') {
      return this.toString();
    }
    this.fromString(value);
    return this;
  }

  alpha(value) {
    if (typeof value === 'undefined' || isNaN(value)) {
      return this.value.a;
    }

    value = parseFloat(value);

    if (value > 1) {
      value = 1;
    } else if (value < 0) {
      value = 0;
    }
    this.value.a = value;
    return this;
  }

  matchString(string) {
    return AsColor.matchString(string);
  }

  fromString(string, updateFormat) {
    if (typeof string === 'string') {
      string = $.trim(string);
      let matched = null;
      let rgb;
      this._valid = false;
      for (let i in ColorStrings) {
        if ((matched = ColorStrings[i].match.exec(string)) !== null) {
          rgb = ColorStrings[i].parse(matched);

          if (rgb) {
            this.set(rgb);
            if(i === 'TRANSPARENT'){
              i = 'HEX';
            }
            this._matchFormat = i;
            if (updateFormat === true) {
              this.format(i);
            }
            break;
          }
        }
      }
    } else if (typeof string === 'object') {
      this.set(string);
    }
    return this;
  }

  format(format) {
    if (typeof format === 'string' && (format = format.toUpperCase()) && typeof ColorStrings[format] !== 'undefined') {
      if (format !== 'TRANSPARENT') {
        this._format = format;
      } else {
        this._format = 'HEX';
      }
    } else if(format === false) {
      this._format = false;
    }
    if(this._format === false){
      return this._matchFormat;
    }
    return this._format;
  }

  toRGBA() {
    return ColorStrings.RGBA.to(this.value, this);
  }

  toRGB() {
    return ColorStrings.RGB.to(this.value, this);
  }

  toHSLA() {
    return ColorStrings.HSLA.to(this.value, this);
  }

  toHSL() {
    return ColorStrings.HSL.to(this.value, this);
  }

  toHEX() {
    return ColorStrings.HEX.to(this.value, this);
  }

  toNAME() {
    return ColorStrings.NAME.to(this.value, this);
  }

  to(format) {
    if (typeof format === 'string' && (format = format.toUpperCase()) && typeof ColorStrings[format] !== 'undefined') {
      return ColorStrings[format].to(this.value, this);
    }
    return this.toString();
  }

  toString() {
    let value = this.value;
    if (!this._valid) {
      value = this.options.invalidValue;

      if (typeof value === 'string') {
        return value;
      }
    }

    if (value.a === 0 && this.options.zeroAlphaAsTransparent) {
      return ColorStrings.TRANSPARENT.to(value, this);
    }

    let format;
    if(this._format === false){
      format = this._matchFormat;
    } else {
      format = this._format;
    }

    if (this.options.reduceAlpha && value.a === 1) {
      switch (format) {
        case 'RGBA':
          format = 'RGB';
          break;
        case 'HSLA':
          format = 'HSL';
          break;
        default:
          break;
      }
    }

    if (value.a !== 1 && format!=='RGBA' && format !=='HSLA' && this.options.alphaConvert){
      if(typeof this.options.alphaConvert === 'string'){
        format = this.options.alphaConvert;
      }
      if(typeof this.options.alphaConvert[format] !== 'undefined'){
        format = this.options.alphaConvert[format];
      }
    }
    return ColorStrings[format].to(value, this);
  }

  get() {
    return this.value;
  }

  set(color) {
    this._valid = true;
    let fromRgb = 0;
    let fromHsv = 0;
    let hsv;
    let rgb;

    for (const i in color) {
      if ('hsv'.includes(i)) {
        fromHsv++;
        this.value[i] = color[i];
      } else if ('rgb'.includes(i)) {
        fromRgb++;
        this.value[i] = color[i];
      } else if (i === 'a') {
        this.value.a = color.a;
      }
    }
    if (fromRgb > fromHsv) {
      hsv = Converter.RGBtoHSV(this.value);
      if (this.value.r === 0 && this.value.g === 0 && this.value.b === 0) {
        // this.value.h = color.h;
      } else {
        this.value.h = hsv.h;
      }

      this.value.s = hsv.s;
      this.value.v = hsv.v;
    } else if (fromHsv > fromRgb) {
      rgb = Converter.HSVtoRGB(this.value);
      this.value.r = rgb.r;
      this.value.g = rgb.g;
      this.value.b = rgb.b;
    }
    return this;
  }

  static matchString(string) {
    if (typeof string === 'string') {
      string = $.trim(string);
      let matched = null;
      let rgb;
      for (const i in ColorStrings) {
        if ((matched = ColorStrings[i].match.exec(string)) !== null) {
          rgb = ColorStrings[i].parse(matched);

          if (rgb) {
            return true;
          }
        }
      }
    }
    return false;
  }

  static setDefaults(options) {
    $.extend(true, DEFAULTS, $.isPlainObject(options) && options);
  }
}


export default AsColor;
