/**
* jQuery asGradient v0.3.2
* https://github.com/amazingSurge/jquery-asGradient
*
* Copyright (c) amazingSurge
* Released under the LGPL-3.0 license
*/
(function(global, factory) {
  if (typeof define === "function" && define.amd) {
    define('AsGradient', ['exports', 'jquery', 'jquery-asColor'], factory);
  } else if (typeof exports !== "undefined") {
    factory(exports, require('jquery'), require('jquery-asColor'));
  } else {
    var mod = {
      exports: {}
    };
    factory(mod.exports, global.jQuery, global.AsColor);
    global.AsGradient = mod.exports;
  }
})(this,

  function(exports, _jquery, _jqueryAsColor) {
    'use strict';

    Object.defineProperty(exports, "__esModule", {
      value: true
    });

    var _jquery2 = _interopRequireDefault(_jquery);

    var _jqueryAsColor2 = _interopRequireDefault(_jqueryAsColor);

    function _interopRequireDefault(obj) {
      return obj && obj.__esModule ? obj : {
        default: obj
      };
    }

    var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ?

      function(obj) {
        return typeof obj;
      }
      :

      function(obj) {
        return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj;
      };

    function _classCallCheck(instance, Constructor) {
      if (!(instance instanceof Constructor)) {
        throw new TypeError("Cannot call a class as a function");
      }
    }

    var _createClass = function() {
      function defineProperties(target, props) {
        for (var i = 0; i < props.length; i++) {
          var descriptor = props[i];
          descriptor.enumerable = descriptor.enumerable || false;
          descriptor.configurable = true;

          if ("value" in descriptor)
            descriptor.writable = true;
          Object.defineProperty(target, descriptor.key, descriptor);
        }
      }

      return function(Constructor, protoProps, staticProps) {
        if (protoProps)
          defineProperties(Constructor.prototype, protoProps);

        if (staticProps)
          defineProperties(Constructor, staticProps);

        return Constructor;
      };
    }();

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
      }
      ;
    }

    function getPrefix() {
      var ua = window.navigator.userAgent;
      var prefix = '';

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
      var flipped = {};

      for (var i in o) {

        if (o.hasOwnProperty(i)) {
          flipped[o[i]] = i;
        }
      }

      return flipped;
    }

    function reverseDirection(direction) {
      var mapping = {
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
      var reg = /^(top|left|right|bottom)$/i;

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

    var angleKeywordMap = flip(keywordAngleMap);

    var RegExpStrings = function() {
      var color = /(?:rgba|rgb|hsla|hsl)\s*\([\s\d\.,%]+\)|#[a-z0-9]{3,6}|[a-z]+/i;
      var position = /\d{1,3}%/i;
      var angle = /(?:to ){0,1}(?:(?:top|left|right|bottom)\s*){1,2}|\d+deg/i;
      var stop = new RegExp('(' + color.source + ')\\s*(' + position.source + '){0,1}', 'i');
      var stops = new RegExp(stop.source, 'gi');
      var parameters = new RegExp('(?:(' + angle.source + ')){0,1}\\s*,{0,1}\\s*(.*?)\\s*', 'i');
      var full = new RegExp('^(-webkit-|-moz-|-ms-|-o-){0,1}(linear|radial|repeating-linear)-gradient\\s*\\(\\s*(' + parameters.source + ')\\s*\\)$', 'i');

      return {
        FULL: full,
        ANGLE: angle,
        COLOR: color,
        POSITION: position,
        STOP: stop,
        STOPS: stops,
        PARAMETERS: new RegExp('^' + parameters.source + '$', 'i')
      };
    }();

    var GradientString = {
      matchString: function matchString(string) {
        var matched = this.parseString(string);

        if (matched && matched.value && matched.value.stops && matched.value.stops.length > 1) {

          return true;
        }

        return false;
      },

      parseString: function parseString(string) {
        string = _jquery2.default.trim(string);
        var matched = void 0;

        if ((matched = RegExpStrings.FULL.exec(string)) !== null) {
          var value = this.parseParameters(matched[3]);

          return {
            prefix: typeof matched[1] === 'undefined' ? null : matched[1],
            type: matched[2],
            value: value
          };
        } else {

          return false;
        }
      },

      parseParameters: function parseParameters(string) {
        var matched = void 0;

        if ((matched = RegExpStrings.PARAMETERS.exec(string)) !== null) {
          var stops = this.parseStops(matched[2]);

          return {
            angle: typeof matched[1] === 'undefined' ? 0 : matched[1],
            stops: stops
          };
        } else {

          return false;
        }
      },

      parseStops: function parseStops(string) {
        var _this = this;

        var matched = void 0;
        var result = [];

        if ((matched = string.match(RegExpStrings.STOPS)) !== null) {

          _jquery2.default.each(matched,

            function(i, item) {
              var stop = _this.parseStop(item);

              if (stop) {
                result.push(stop);
              }
            }
          );

          return result;
        } else {

          return false;
        }
      },

      formatStops: function formatStops(stops, cleanPosition) {
        var stop = void 0;
        var output = [];
        var positions = [];
        var colors = [];
        var position = void 0;

        for (var i = 0; i < stops.length; i++) {
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

        positions = function(data) {
          var start = null;
          var average = void 0;

          for (var _i = 0; _i < data.length; _i++) {

            if (isNaN(data[_i])) {

              if (start === null) {
                start = _i;
                continue;
              }
            } else if (start) {
              average = (data[_i] - data[start - 1]) / (_i - start + 1);

              for (var j = start; j < _i; j++) {
                data[j] = data[start - 1] + (j - start + 1) * average;
              }
              start = null;
            }
          }

          return data;
        }(positions);

        for (var x = 0; x < stops.length; x++) {

          if (cleanPosition && (x === 0 && positions[x] === 0 || x === stops.length - 1 && positions[x] === 1)) {
            position = '';
          } else {
            position = ' ' + this.formatPosition(positions[x]);
          }

          output.push(colors[x] + position);
        }

        return output.join(', ');
      },

      parseStop: function parseStop(string) {
        var matched = void 0;

        if ((matched = RegExpStrings.STOP.exec(string)) !== null) {
          var position = this.parsePosition(matched[2]);

          return {
            color: matched[1],
            position: position
          };
        } else {

          return false;
        }
      },

      parsePosition: function parsePosition(string) {
        if (typeof string === 'string' && string.substr(-1) === '%') {
          string = parseFloat(string.slice(0, -1) / 100);
        }

        if (typeof string !== 'undefined' && string !== null) {

          return parseFloat(string, 10);
        } else {

          return null;
        }
      },

      formatPosition: function formatPosition(value) {
        return parseInt(value * 100, 10) + '%';
      },

      parseAngle: function parseAngle(string, notStandard) {
        if (typeof string === 'string' && string.includes('deg')) {
          string = string.replace('deg', '');
        }

        if (!isNaN(string)) {

          if (notStandard) {
            string = this.fixOldAngle(string);
          }
        }

        if (typeof string === 'string') {
          var directions = string.split(' ');

          var filtered = [];

          for (var i in directions) {

            if (isDirection(directions[i])) {
              filtered.push(directions[i].toLowerCase());
            }
          }
          var keyword = filtered.join(' ');

          if (!string.includes('to ')) {
            keyword = reverseDirection(keyword);
          }
          keyword = 'to ' + keyword;

          if (keywordAngleMap.hasOwnProperty(keyword)) {
            string = keywordAngleMap[keyword];
          }
        }
        var value = parseFloat(string, 10);

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

      fixOldAngle: function fixOldAngle(value) {
        value = parseFloat(value);
        value = Math.abs(450 - value) % 360;
        value = parseFloat(value.toFixed(3));

        return value;
      },

      formatAngle: function formatAngle(value, notStandard, useKeyword) {
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
          value = value + 'deg';
        }

        return value;
      }
    };

    var ColorStop = function() {
      function ColorStop(color, position, gradient) {
        _classCallCheck(this, ColorStop);

        this.color = (0, _jqueryAsColor2.default)(color, gradient.options.color);
        this.position = GradientString.parsePosition(position);
        this.id = ++gradient._stopIdCount;
        this.gradient = gradient;
      }

      _createClass(ColorStop, [{
        key: 'setPosition',
        value: function setPosition(string) {
          var position = GradientString.parsePosition(string);

          if (this.position !== position) {
            this.position = position;
            this.gradient.reorder();
          }
        }
      }, {
        key: 'setColor',
        value: function setColor(string) {
          this.color.fromString(string);
        }
      }, {
        key: 'remove',
        value: function remove() {
          this.gradient.removeById(this.id);
        }
      }]);

      return ColorStop;
    }();

    var GradientTypes = {
      LINEAR: {
        parse: function parse(result) {
          return {
            r: result[1].substr(-1) === '%' ? parseInt(result[1].slice(0, -1) * 2.55, 10) : parseInt(result[1], 10),
            g: result[2].substr(-1) === '%' ? parseInt(result[2].slice(0, -1) * 2.55, 10) : parseInt(result[2], 10),
            b: result[3].substr(-1) === '%' ? parseInt(result[3].slice(0, -1) * 2.55, 10) : parseInt(result[3], 10),
            a: 1
          };
        },
        to: function to(gradient, instance, prefix) {
          if (gradient.stops.length === 0) {

            return instance.options.emptyString;
          }

          if (gradient.stops.length === 1) {

            return gradient.stops[0].color.to(instance.options.degradationFormat);
          }

          var standard = instance.options.forceStandard;
          var _prefix = instance._prefix;

          if (!_prefix) {
            standard = true;
          }

          if (prefix && -1 !== _jquery2.default.inArray(prefix, instance.options.prefixes)) {
            standard = false;
            _prefix = prefix;
          }

          var angle = GradientString.formatAngle(gradient.angle, !standard, instance.options.angleUseKeyword);
          var stops = GradientString.formatStops(gradient.stops, instance.options.cleanPosition);

          var output = 'linear-gradient(' + angle + ', ' + stops + ')';

          if (standard) {

            return output;
          } else {

            return _prefix + output;
          }
        }
      }
    };

    var AsGradient = function() {
      function AsGradient(string, options) {
        _classCallCheck(this, AsGradient);

        if ((typeof string === 'undefined' ? 'undefined' : _typeof(string)) === 'object' && typeof options === 'undefined') {
          options = string;
          string = undefined;
        }
        this.value = {
          angle: 0,
          stops: []
        };
        this.options = _jquery2.default.extend(true, {}, DEFAULTS, options);

        this._type = 'LINEAR';
        this._prefix = null;
        this.length = this.value.stops.length;
        this.current = 0;
        this._stopIdCount = 0;

        this.init(string);
      }

      _createClass(AsGradient, [{
        key: 'init',
        value: function init(string) {
          if (string) {
            this.fromString(string);
          }
        }
      }, {
        key: 'val',
        value: function val(value) {
          if (typeof value === 'undefined') {

            return this.toString();
          } else {
            this.fromString(value);

            return this;
          }
        }
      }, {
        key: 'angle',
        value: function angle(value) {
          if (typeof value === 'undefined') {

            return this.value.angle;
          } else {
            this.value.angle = GradientString.parseAngle(value);

            return this;
          }
        }
      }, {
        key: 'append',
        value: function append(color, position) {
          return this.insert(color, position, this.length);
        }
      }, {
        key: 'reorder',
        value: function reorder() {
          if (this.length < 2) {

            return;
          }

          this.value.stops = this.value.stops.sort(

            function(a, b) {
              return a.position - b.position;
            }
          );
        }
      }, {
        key: 'insert',
        value: function insert(color, position, index) {
          if (typeof index === 'undefined') {
            index = this.current;
          }

          var stop = new ColorStop(color, position, this);

          this.value.stops.splice(index, 0, stop);

          this.length = this.length + 1;
          this.current = index;

          return stop;
        }
      }, {
        key: 'getById',
        value: function getById(id) {
          if (this.length > 0) {

            for (var i in this.value.stops) {

              if (id === this.value.stops[i].id) {

                return this.value.stops[i];
              }
            }
          }

          return false;
        }
      }, {
        key: 'removeById',
        value: function removeById(id) {
          var index = this.getIndexById(id);

          if (index) {
            this.remove(index);
          }
        }
      }, {
        key: 'getIndexById',
        value: function getIndexById(id) {
          var index = 0;

          for (var i in this.value.stops) {

            if (id === this.value.stops[i].id) {

              return index;
            }
            index++;
          }

          return false;
        }
      }, {
        key: 'getCurrent',
        value: function getCurrent() {
          return this.value.stops[this.current];
        }
      }, {
        key: 'setCurrentById',
        value: function setCurrentById(id) {
          var index = 0;

          for (var i in this.value.stops) {

            if (this.value.stops[i].id !== id) {
              index++;
            } else {
              this.current = index;
            }
          }
        }
      }, {
        key: 'get',
        value: function get(index) {
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
      }, {
        key: 'remove',
        value: function remove(index) {
          if (typeof index === 'undefined') {
            index = this.current;
          }

          if (index >= 0 && index < this.length) {
            this.value.stops.splice(index, 1);
            this.length = this.length - 1;
            this.current = index - 1;
          }
        }
      }, {
        key: 'empty',
        value: function empty() {
          this.value.stops = [];
          this.length = 0;
          this.current = 0;
        }
      }, {
        key: 'reset',
        value: function reset() {
          this.value._angle = 0;
          this.empty();
          this._prefix = null;
          this._type = 'LINEAR';
        }
      }, {
        key: 'type',
        value: function type(_type) {
          if (typeof _type === 'string' && (_type = _type.toUpperCase()) && typeof GradientTypes[_type] !== 'undefined') {
            this._type = _type;

            return this;
          } else {

            return this._type;
          }
        }
      }, {
        key: 'fromString',
        value: function fromString(string) {
          var _this2 = this;

          this.reset();

          var result = GradientString.parseString(string);

          if (result) {
            this._prefix = result.prefix;
            this.type(result.type);

            if (result.value) {
              this.value.angle = GradientString.parseAngle(result.value.angle, this._prefix !== null);

              _jquery2.default.each(result.value.stops,

                function(i, stop) {
                  _this2.append(stop.color, stop.position);
                }
              );
            }
          }
        }
      }, {
        key: 'toString',
        value: function toString(prefix) {
          if (prefix === true) {
            prefix = getPrefix();
          }

          return GradientTypes[this.type()].to(this.value, this, prefix);
        }
      }, {
        key: 'matchString',
        value: function matchString(string) {
          return GradientString.matchString(string);
        }
      }, {
        key: 'toStringWithAngle',
        value: function toStringWithAngle(angle, prefix) {
          var value = _jquery2.default.extend(true, {}, this.value);
          value.angle = GradientString.parseAngle(angle);

          if (prefix === true) {
            prefix = getPrefix();
          }

          return GradientTypes[this.type()].to(value, this, prefix);
        }
      }, {
        key: 'getPrefixedStrings',
        value: function getPrefixedStrings() {
          var strings = [];

          for (var i in this.options.prefixes) {

            if (Object.hasOwnProperty.call(this.options.prefixes, i)) {
              strings.push(this.toString(this.options.prefixes[i]));
            }
          }

          return strings;
        }
      }], [{
        key: 'setDefaults',
        value: function setDefaults(options) {
          _jquery2.default.extend(true, DEFAULTS, _jquery2.default.isPlainObject(options) && options);
        }
      }]);

      return AsGradient;
    }();

    var info = {
      version: '0.3.2'
    };

    var OtherAsGradient = _jquery2.default.asGradient;

    var jQueryAsGradient = function jQueryAsGradient() {
      for (var _len = arguments.length, args = Array(_len), _key = 0; _key < _len; _key++) {
        args[_key] = arguments[_key];
      }

      return new (Function.prototype.bind.apply(AsGradient, [null].concat(args)))();
    };

    _jquery2.default.asGradient = jQueryAsGradient;
    _jquery2.default.asGradient.Constructor = AsGradient;

    _jquery2.default.extend(_jquery2.default.asGradient, {
      setDefaults: AsGradient.setDefaults,
      noConflict: function noConflict() {
        _jquery2.default.asGradient = OtherAsGradient;

        return jQueryAsGradient;
      }
    }, GradientString, info);

    var main = _jquery2.default.asGradient;

    exports.default = main;
  }
);