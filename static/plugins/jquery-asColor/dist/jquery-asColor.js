/**
* jQuery asColor v0.3.6
* https://github.com/amazingSurge/asColor
*
* Copyright (c) amazingSurge
* Released under the LGPL-3.0 license
*/
(function(global, factory) {
  if (typeof define === 'function' && define.amd) {
    define('AsColor', ['exports', 'jquery'], factory);
  } else if (typeof exports !== 'undefined') {
    factory(exports, require('jquery'));
  } else {
    var mod = {
      exports: {}
    };
    factory(mod.exports, global.jQuery);
    global.AsColor = mod.exports;
  }
})(this, function(exports, _jquery) {
  'use strict';

  Object.defineProperty(exports, '__esModule', {
    value: true
  });

  var _jquery2 = _interopRequireDefault(_jquery);

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule
      ? obj
      : {
          default: obj
        };
  }

  var _typeof =
    typeof Symbol === 'function' && typeof Symbol.iterator === 'symbol'
      ? function(obj) {
          return typeof obj;
        }
      : function(obj) {
          return obj &&
          typeof Symbol === 'function' &&
          obj.constructor === Symbol &&
          obj !== Symbol.prototype
            ? 'symbol'
            : typeof obj;
        };

  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError('Cannot call a class as a function');
    }
  }

  var _createClass = (function() {
    function defineProperties(target, props) {
      for (var i = 0; i < props.length; i++) {
        var descriptor = props[i];
        descriptor.enumerable = descriptor.enumerable || false;
        descriptor.configurable = true;
        if ('value' in descriptor) descriptor.writable = true;
        Object.defineProperty(target, descriptor.key, descriptor);
      }
    }

    return function(Constructor, protoProps, staticProps) {
      if (protoProps) defineProperties(Constructor.prototype, protoProps);
      if (staticProps) defineProperties(Constructor, staticProps);
      return Constructor;
    };
  })();

  var DEFAULTS = {
    format: false,
    shortenHex: false,
    hexUseName: false,
    reduceAlpha: false,
    alphaConvert: {
      // or false will disable convert
      RGB: 'RGBA',
      HSL: 'HSLA',
      HEX: 'RGBA',
      NAMESPACE: 'RGBA'
    },
    nameDegradation: 'HEX',
    invalidValue: '',
    zeroAlphaAsTransparent: true
  };

  function expandHex(hex) {
    if (hex.indexOf('#') === 0) {
      hex = hex.substr(1);
    }
    if (!hex) {
      return null;
    }
    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    return hex.length === 6 ? '#' + hex : null;
  }

  function shrinkHex(hex) {
    if (hex.indexOf('#') === 0) {
      hex = hex.substr(1);
    }
    if (
      hex.length === 6 &&
      hex[0] === hex[1] &&
      hex[2] === hex[3] &&
      hex[4] === hex[5]
    ) {
      hex = hex[0] + hex[2] + hex[4];
    }
    return '#' + hex;
  }

  function parseIntFromHex(val) {
    return parseInt(val, 16);
  }

  function isPercentage(n) {
    return typeof n === 'string' && n.indexOf('%') === n.length - 1;
  }

  function conventPercentageToRgb(n) {
    return parseInt(Math.round(n.slice(0, -1) * 2.55), 10);
  }

  function convertPercentageToFloat(n) {
    return parseFloat(n.slice(0, -1) / 100, 10);
  }

  function flip(o) {
    var flipped = {};
    for (var i in o) {
      if (o.hasOwnProperty(i)) {
        flipped[o[i]] = i;
      }
    }
    return flipped;
  }

  var NAMES = {
    aliceblue: 'f0f8ff',
    antiquewhite: 'faebd7',
    aqua: '0ff',
    aquamarine: '7fffd4',
    azure: 'f0ffff',
    beige: 'f5f5dc',
    bisque: 'ffe4c4',
    black: '000',
    blanchedalmond: 'ffebcd',
    blue: '00f',
    blueviolet: '8a2be2',
    brown: 'a52a2a',
    burlywood: 'deb887',
    burntsienna: 'ea7e5d',
    cadetblue: '5f9ea0',
    chartreuse: '7fff00',
    chocolate: 'd2691e',
    coral: 'ff7f50',
    cornflowerblue: '6495ed',
    cornsilk: 'fff8dc',
    crimson: 'dc143c',
    cyan: '0ff',
    darkblue: '00008b',
    darkcyan: '008b8b',
    darkgoldenrod: 'b8860b',
    darkgray: 'a9a9a9',
    darkgreen: '006400',
    darkgrey: 'a9a9a9',
    darkkhaki: 'bdb76b',
    darkmagenta: '8b008b',
    darkolivegreen: '556b2f',
    darkorange: 'ff8c00',
    darkorchid: '9932cc',
    darkred: '8b0000',
    darksalmon: 'e9967a',
    darkseagreen: '8fbc8f',
    darkslateblue: '483d8b',
    darkslategray: '2f4f4f',
    darkslategrey: '2f4f4f',
    darkturquoise: '00ced1',
    darkviolet: '9400d3',
    deeppink: 'ff1493',
    deepskyblue: '00bfff',
    dimgray: '696969',
    dimgrey: '696969',
    dodgerblue: '1e90ff',
    firebrick: 'b22222',
    floralwhite: 'fffaf0',
    forestgreen: '228b22',
    fuchsia: 'f0f',
    gainsboro: 'dcdcdc',
    ghostwhite: 'f8f8ff',
    gold: 'ffd700',
    goldenrod: 'daa520',
    gray: '808080',
    green: '008000',
    greenyellow: 'adff2f',
    grey: '808080',
    honeydew: 'f0fff0',
    hotpink: 'ff69b4',
    indianred: 'cd5c5c',
    indigo: '4b0082',
    ivory: 'fffff0',
    khaki: 'f0e68c',
    lavender: 'e6e6fa',
    lavenderblush: 'fff0f5',
    lawngreen: '7cfc00',
    lemonchiffon: 'fffacd',
    lightblue: 'add8e6',
    lightcoral: 'f08080',
    lightcyan: 'e0ffff',
    lightgoldenrodyellow: 'fafad2',
    lightgray: 'd3d3d3',
    lightgreen: '90ee90',
    lightgrey: 'd3d3d3',
    lightpink: 'ffb6c1',
    lightsalmon: 'ffa07a',
    lightseagreen: '20b2aa',
    lightskyblue: '87cefa',
    lightslategray: '789',
    lightslategrey: '789',
    lightsteelblue: 'b0c4de',
    lightyellow: 'ffffe0',
    lime: '0f0',
    limegreen: '32cd32',
    linen: 'faf0e6',
    magenta: 'f0f',
    maroon: '800000',
    mediumaquamarine: '66cdaa',
    mediumblue: '0000cd',
    mediumorchid: 'ba55d3',
    mediumpurple: '9370db',
    mediumseagreen: '3cb371',
    mediumslateblue: '7b68ee',
    mediumspringgreen: '00fa9a',
    mediumturquoise: '48d1cc',
    mediumvioletred: 'c71585',
    midnightblue: '191970',
    mintcream: 'f5fffa',
    mistyrose: 'ffe4e1',
    moccasin: 'ffe4b5',
    navajowhite: 'ffdead',
    navy: '000080',
    oldlace: 'fdf5e6',
    olive: '808000',
    olivedrab: '6b8e23',
    orange: 'ffa500',
    orangered: 'ff4500',
    orchid: 'da70d6',
    palegoldenrod: 'eee8aa',
    palegreen: '98fb98',
    paleturquoise: 'afeeee',
    palevioletred: 'db7093',
    papayawhip: 'ffefd5',
    peachpuff: 'ffdab9',
    peru: 'cd853f',
    pink: 'ffc0cb',
    plum: 'dda0dd',
    powderblue: 'b0e0e6',
    purple: '800080',
    red: 'f00',
    rosybrown: 'bc8f8f',
    royalblue: '4169e1',
    saddlebrown: '8b4513',
    salmon: 'fa8072',
    sandybrown: 'f4a460',
    seagreen: '2e8b57',
    seashell: 'fff5ee',
    sienna: 'a0522d',
    silver: 'c0c0c0',
    skyblue: '87ceeb',
    slateblue: '6a5acd',
    slategray: '708090',
    slategrey: '708090',
    snow: 'fffafa',
    springgreen: '00ff7f',
    steelblue: '4682b4',
    tan: 'd2b48c',
    teal: '008080',
    thistle: 'd8bfd8',
    tomato: 'ff6347',
    turquoise: '40e0d0',
    violet: 'ee82ee',
    wheat: 'f5deb3',
    white: 'fff',
    whitesmoke: 'f5f5f5',
    yellow: 'ff0',
    yellowgreen: '9acd32'
  };

  /* eslint no-bitwise: "off" */
  var hexNames = flip(NAMES);

  var Converter = {
    HSLtoRGB: function HSLtoRGB(hsl) {
      var h = hsl.h / 360;
      var s = hsl.s;
      var l = hsl.l;
      var m1 = void 0;
      var m2 = void 0;
      var rgb = void 0;
      if (l <= 0.5) {
        m2 = l * (s + 1);
      } else {
        m2 = l + s - l * s;
      }
      m1 = l * 2 - m2;
      rgb = {
        r: this.hueToRGB(m1, m2, h + 1 / 3),
        g: this.hueToRGB(m1, m2, h),
        b: this.hueToRGB(m1, m2, h - 1 / 3)
      };
      if (typeof hsl.a !== 'undefined') {
        rgb.a = hsl.a;
      }
      if (hsl.l === 0) {
        rgb.h = hsl.h;
      }
      if (hsl.l === 1) {
        rgb.h = hsl.h;
      }
      return rgb;
    },

    hueToRGB: function hueToRGB(m1, m2, h) {
      var v = void 0;
      if (h < 0) {
        h += 1;
      } else if (h > 1) {
        h -= 1;
      }
      if (h * 6 < 1) {
        v = m1 + (m2 - m1) * h * 6;
      } else if (h * 2 < 1) {
        v = m2;
      } else if (h * 3 < 2) {
        v = m1 + (m2 - m1) * (2 / 3 - h) * 6;
      } else {
        v = m1;
      }
      return Math.round(v * 255);
    },

    RGBtoHSL: function RGBtoHSL(rgb) {
      var r = rgb.r / 255;
      var g = rgb.g / 255;
      var b = rgb.b / 255;
      var min = Math.min(r, g, b);
      var max = Math.max(r, g, b);
      var diff = max - min;
      var add = max + min;
      var l = add * 0.5;
      var h = void 0;
      var s = void 0;

      if (min === max) {
        h = 0;
      } else if (r === max) {
        h = 60 * (g - b) / diff + 360;
      } else if (g === max) {
        h = 60 * (b - r) / diff + 120;
      } else {
        h = 60 * (r - g) / diff + 240;
      }
      if (diff === 0) {
        s = 0;
      } else if (l <= 0.5) {
        s = diff / add;
      } else {
        s = diff / (2 - add);
      }

      return {
        h: Math.round(h) % 360,
        s: s,
        l: l
      };
    },

    RGBtoHEX: function RGBtoHEX(rgb) {
      var hex = [rgb.r.toString(16), rgb.g.toString(16), rgb.b.toString(16)];

      _jquery2.default.each(hex, function(nr, val) {
        if (val.length === 1) {
          hex[nr] = '0' + val;
        }
      });
      return '#' + hex.join('');
    },

    HSLtoHEX: function HSLtoHEX(hsl) {
      var rgb = this.HSLtoRGB(hsl);
      return this.RGBtoHEX(rgb);
    },

    HSVtoHEX: function HSVtoHEX(hsv) {
      var rgb = this.HSVtoRGB(hsv);
      return this.RGBtoHEX(rgb);
    },

    RGBtoHSV: function RGBtoHSV(rgb) {
      var r = rgb.r / 255;
      var g = rgb.g / 255;
      var b = rgb.b / 255;
      var max = Math.max(r, g, b);
      var min = Math.min(r, g, b);
      var h = void 0;
      var s = void 0;
      var v = max;
      var diff = max - min;
      s = max === 0 ? 0 : diff / max;
      if (max === min) {
        h = 0;
      } else {
        switch (max) {
          case r: {
            h = (g - b) / diff + (g < b ? 6 : 0);
            break;
          }
          case g: {
            h = (b - r) / diff + 2;
            break;
          }
          case b: {
            h = (r - g) / diff + 4;
            break;
          }
          default: {
            break;
          }
        }
        h /= 6;
      }

      return {
        h: Math.round(h * 360),
        s: s,
        v: v
      };
    },

    HSVtoRGB: function HSVtoRGB(hsv) {
      var r = void 0;
      var g = void 0;
      var b = void 0;
      var h = (hsv.h % 360) / 60;
      var s = hsv.s;
      var v = hsv.v;
      var c = v * s;
      var x = c * (1 - Math.abs(h % 2 - 1));

      r = g = b = v - c;
      h = ~~h;

      r += [c, x, 0, 0, x, c][h];
      g += [x, c, c, x, 0, 0][h];
      b += [0, 0, x, c, c, x][h];

      var rgb = {
        r: Math.round(r * 255),
        g: Math.round(g * 255),
        b: Math.round(b * 255)
      };

      if (typeof hsv.a !== 'undefined') {
        rgb.a = hsv.a;
      }

      if (hsv.v === 0) {
        rgb.h = hsv.h;
      }

      if (hsv.v === 1 && hsv.s === 0) {
        rgb.h = hsv.h;
      }

      return rgb;
    },

    HEXtoRGB: function HEXtoRGB(hex) {
      if (hex.length === 4) {
        hex = expandHex(hex);
      }
      return {
        r: parseIntFromHex(hex.substr(1, 2)),
        g: parseIntFromHex(hex.substr(3, 2)),
        b: parseIntFromHex(hex.substr(5, 2))
      };
    },

    isNAME: function isNAME(string) {
      if (NAMES.hasOwnProperty(string)) {
        return true;
      }
      return false;
    },

    NAMEtoHEX: function NAMEtoHEX(name) {
      if (NAMES.hasOwnProperty(name)) {
        return '#' + NAMES[name];
      }
      return null;
    },

    NAMEtoRGB: function NAMEtoRGB(name) {
      var hex = this.NAMEtoHEX(name);

      if (hex) {
        return this.HEXtoRGB(hex);
      }
      return null;
    },

    hasNAME: function hasNAME(rgb) {
      var hex = this.RGBtoHEX(rgb);

      hex = shrinkHex(hex);

      if (hex.indexOf('#') === 0) {
        hex = hex.substr(1);
      }

      if (hexNames.hasOwnProperty(hex)) {
        return hexNames[hex];
      }
      return false;
    },

    RGBtoNAME: function RGBtoNAME(rgb) {
      var hasName = this.hasNAME(rgb);
      if (hasName) {
        return hasName;
      }

      return null;
    }
  };

  var CSS_INTEGER = '[-\\+]?\\d+%?';
  var CSS_NUMBER = '[-\\+]?\\d*\\.\\d+%?';
  var CSS_UNIT = '(?:' + CSS_NUMBER + ')|(?:' + CSS_INTEGER + ')';

  var PERMISSIVE_MATCH3 =
    '[\\s|\\(]+(' +
    CSS_UNIT +
    ')[,|\\s]+(' +
    CSS_UNIT +
    ')[,|\\s]+(' +
    CSS_UNIT +
    ')\\s*\\)';
  var PERMISSIVE_MATCH4 =
    '[\\s|\\(]+(' +
    CSS_UNIT +
    ')[,|\\s]+(' +
    CSS_UNIT +
    ')[,|\\s]+(' +
    CSS_UNIT +
    ')[,|\\s]+(' +
    CSS_UNIT +
    ')\\s*\\)';

  var ColorStrings = {
    RGB: {
      match: new RegExp('^rgb' + PERMISSIVE_MATCH3 + '$', 'i'),
      parse: function parse(result) {
        return {
          r: isPercentage(result[1])
            ? conventPercentageToRgb(result[1])
            : parseInt(result[1], 10),
          g: isPercentage(result[2])
            ? conventPercentageToRgb(result[2])
            : parseInt(result[2], 10),
          b: isPercentage(result[3])
            ? conventPercentageToRgb(result[3])
            : parseInt(result[3], 10),
          a: 1
        };
      },
      to: function to(color) {
        return 'rgb(' + color.r + ', ' + color.g + ', ' + color.b + ')';
      }
    },
    RGBA: {
      match: new RegExp('^rgba' + PERMISSIVE_MATCH4 + '$', 'i'),
      parse: function parse(result) {
        return {
          r: isPercentage(result[1])
            ? conventPercentageToRgb(result[1])
            : parseInt(result[1], 10),
          g: isPercentage(result[2])
            ? conventPercentageToRgb(result[2])
            : parseInt(result[2], 10),
          b: isPercentage(result[3])
            ? conventPercentageToRgb(result[3])
            : parseInt(result[3], 10),
          a: isPercentage(result[4])
            ? convertPercentageToFloat(result[4])
            : parseFloat(result[4], 10)
        };
      },
      to: function to(color) {
        return (
          'rgba(' +
          color.r +
          ', ' +
          color.g +
          ', ' +
          color.b +
          ', ' +
          color.a +
          ')'
        );
      }
    },
    HSL: {
      match: new RegExp('^hsl' + PERMISSIVE_MATCH3 + '$', 'i'),
      parse: function parse(result) {
        var hsl = {
          h: (result[1] % 360 + 360) % 360,
          s: isPercentage(result[2])
            ? convertPercentageToFloat(result[2])
            : parseFloat(result[2], 10),
          l: isPercentage(result[3])
            ? convertPercentageToFloat(result[3])
            : parseFloat(result[3], 10),
          a: 1
        };

        return Converter.HSLtoRGB(hsl);
      },
      to: function to(color) {
        var hsl = Converter.RGBtoHSL(color);
        return (
          'hsl(' +
          parseInt(hsl.h, 10) +
          ', ' +
          Math.round(hsl.s * 100) +
          '%, ' +
          Math.round(hsl.l * 100) +
          '%)'
        );
      }
    },
    HSLA: {
      match: new RegExp('^hsla' + PERMISSIVE_MATCH4 + '$', 'i'),
      parse: function parse(result) {
        var hsla = {
          h: (result[1] % 360 + 360) % 360,
          s: isPercentage(result[2])
            ? convertPercentageToFloat(result[2])
            : parseFloat(result[2], 10),
          l: isPercentage(result[3])
            ? convertPercentageToFloat(result[3])
            : parseFloat(result[3], 10),
          a: isPercentage(result[4])
            ? convertPercentageToFloat(result[4])
            : parseFloat(result[4], 10)
        };

        return Converter.HSLtoRGB(hsla);
      },
      to: function to(color) {
        var hsl = Converter.RGBtoHSL(color);
        return (
          'hsla(' +
          parseInt(hsl.h, 10) +
          ', ' +
          Math.round(hsl.s * 100) +
          '%, ' +
          Math.round(hsl.l * 100) +
          '%, ' +
          color.a +
          ')'
        );
      }
    },
    HEX: {
      match: /^#([a-f0-9]{6}|[a-f0-9]{3})$/i,
      parse: function parse(result) {
        var hex = result[0];
        var rgb = Converter.HEXtoRGB(hex);
        return {
          r: rgb.r,
          g: rgb.g,
          b: rgb.b,
          a: 1
        };
      },
      to: function to(color, instance) {
        var hex = Converter.RGBtoHEX(color);

        if (instance) {
          if (instance.options.hexUseName) {
            var hasName = Converter.hasNAME(color);
            if (hasName) {
              return hasName;
            }
          }
          if (instance.options.shortenHex) {
            hex = shrinkHex(hex);
          }
        }
        return '' + hex;
      }
    },
    TRANSPARENT: {
      match: /^transparent$/i,
      parse: function parse() {
        return {
          r: 0,
          g: 0,
          b: 0,
          a: 0
        };
      },
      to: function to() {
        return 'transparent';
      }
    },
    NAME: {
      match: /^\w+$/i,
      parse: function parse(result) {
        var rgb = Converter.NAMEtoRGB(result[0]);
        if (rgb) {
          return {
            r: rgb.r,
            g: rgb.g,
            b: rgb.b,
            a: 1
          };
        }

        return null;
      },
      to: function to(color, instance) {
        var name = Converter.RGBtoNAME(color);

        if (name) {
          return name;
        }

        return ColorStrings[instance.options.nameDegradation.toUpperCase()].to(
          color
        );
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

  var AsColor = (function() {
    function AsColor(string, options) {
      _classCallCheck(this, AsColor);

      if (
        (typeof string === 'undefined' ? 'undefined' : _typeof(string)) ===
          'object' &&
        typeof options === 'undefined'
      ) {
        options = string;
        string = undefined;
      }
      if (typeof options === 'string') {
        options = {
          format: options
        };
      }
      this.options = _jquery2.default.extend(true, {}, DEFAULTS, options);
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

    _createClass(
      AsColor,
      [
        {
          key: 'init',
          value: function init(string) {
            this.format(this.options.format);
            this.fromString(string);
            return this;
          }
        },
        {
          key: 'isValid',
          value: function isValid() {
            return this._valid;
          }
        },
        {
          key: 'val',
          value: function val(value) {
            if (typeof value === 'undefined') {
              return this.toString();
            }
            this.fromString(value);
            return this;
          }
        },
        {
          key: 'alpha',
          value: function alpha(value) {
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
        },
        {
          key: 'matchString',
          value: function matchString(string) {
            return AsColor.matchString(string);
          }
        },
        {
          key: 'fromString',
          value: function fromString(string, updateFormat) {
            if (typeof string === 'string') {
              string = _jquery2.default.trim(string);
              var matched = null;
              var rgb = void 0;
              this._valid = false;
              for (var i in ColorStrings) {
                if ((matched = ColorStrings[i].match.exec(string)) !== null) {
                  rgb = ColorStrings[i].parse(matched);

                  if (rgb) {
                    this.set(rgb);
                    if (i === 'TRANSPARENT') {
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
            } else if (
              (typeof string === 'undefined'
                ? 'undefined'
                : _typeof(string)) === 'object'
            ) {
              this.set(string);
            }
            return this;
          }
        },
        {
          key: 'format',
          value: function format(_format) {
            if (
              typeof _format === 'string' &&
              (_format = _format.toUpperCase()) &&
              typeof ColorStrings[_format] !== 'undefined'
            ) {
              if (_format !== 'TRANSPARENT') {
                this._format = _format;
              } else {
                this._format = 'HEX';
              }
            } else if (_format === false) {
              this._format = false;
            }
            if (this._format === false) {
              return this._matchFormat;
            }
            return this._format;
          }
        },
        {
          key: 'toRGBA',
          value: function toRGBA() {
            return ColorStrings.RGBA.to(this.value, this);
          }
        },
        {
          key: 'toRGB',
          value: function toRGB() {
            return ColorStrings.RGB.to(this.value, this);
          }
        },
        {
          key: 'toHSLA',
          value: function toHSLA() {
            return ColorStrings.HSLA.to(this.value, this);
          }
        },
        {
          key: 'toHSL',
          value: function toHSL() {
            return ColorStrings.HSL.to(this.value, this);
          }
        },
        {
          key: 'toHEX',
          value: function toHEX() {
            return ColorStrings.HEX.to(this.value, this);
          }
        },
        {
          key: 'toNAME',
          value: function toNAME() {
            return ColorStrings.NAME.to(this.value, this);
          }
        },
        {
          key: 'to',
          value: function to(format) {
            if (
              typeof format === 'string' &&
              (format = format.toUpperCase()) &&
              typeof ColorStrings[format] !== 'undefined'
            ) {
              return ColorStrings[format].to(this.value, this);
            }
            return this.toString();
          }
        },
        {
          key: 'toString',
          value: function toString() {
            var value = this.value;
            if (!this._valid) {
              value = this.options.invalidValue;

              if (typeof value === 'string') {
                return value;
              }
            }

            if (value.a === 0 && this.options.zeroAlphaAsTransparent) {
              return ColorStrings.TRANSPARENT.to(value, this);
            }

            var format = void 0;
            if (this._format === false) {
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

            if (
              value.a !== 1 &&
              format !== 'RGBA' &&
              format !== 'HSLA' &&
              this.options.alphaConvert
            ) {
              if (typeof this.options.alphaConvert === 'string') {
                format = this.options.alphaConvert;
              }
              if (typeof this.options.alphaConvert[format] !== 'undefined') {
                format = this.options.alphaConvert[format];
              }
            }
            return ColorStrings[format].to(value, this);
          }
        },
        {
          key: 'get',
          value: function get() {
            return this.value;
          }
        },
        {
          key: 'set',
          value: function set(color) {
            this._valid = true;
            var fromRgb = 0;
            var fromHsv = 0;
            var hsv = void 0;
            var rgb = void 0;

            for (var i in color) {
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
              if (
                this.value.r === 0 &&
                this.value.g === 0 &&
                this.value.b === 0
              ) {
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
        }
      ],
      [
        {
          key: 'matchString',
          value: function matchString(string) {
            if (typeof string === 'string') {
              string = _jquery2.default.trim(string);
              var matched = null;
              var rgb = void 0;
              for (var i in ColorStrings) {
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
        },
        {
          key: 'setDefaults',
          value: function setDefaults(options) {
            _jquery2.default.extend(
              true,
              DEFAULTS,
              _jquery2.default.isPlainObject(options) && options
            );
          }
        }
      ]
    );

    return AsColor;
  })();

  var info = {
    version: '0.3.6'
  };

  var OtherAsColor = _jquery2.default.asColor;

  var jQueryAsColor = function jQueryAsColor() {
    for (
      var _len = arguments.length, args = Array(_len), _key = 0;
      _key < _len;
      _key++
    ) {
      args[_key] = arguments[_key];
    }

    return new (Function.prototype.bind.apply(AsColor, [null].concat(args)))();
  };

  _jquery2.default.asColor = jQueryAsColor;
  _jquery2.default.asColor.Constructor = AsColor;

  _jquery2.default.extend(
    _jquery2.default.asColor,
    {
      matchString: AsColor.matchString,
      setDefaults: AsColor.setDefaults,
      noConflict: function noConflict() {
        _jquery2.default.asColor = OtherAsColor;
        return jQueryAsColor;
      }
    },
    Converter,
    info
  );

  var main = _jquery2.default.asColor;

  exports.default = main;
});
