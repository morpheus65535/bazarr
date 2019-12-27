/**
* asColorPicker v0.4.4
* https://github.com/amazingSurge/jquery-asColorPicker
*
* Copyright (c) amazingSurge
* Released under the LGPL-3.0 license
*/
(function(global, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['jquery', 'jquery-asColor', 'jquery-asGradient'], factory);
  } else if (typeof exports !== 'undefined') {
    factory(
      require('jquery'),
      require('jquery-asColor'),
      require('jquery-asGradient')
    );
  } else {
    var mod = {
      exports: {}
    };
    factory(global.jQuery, global.AsColor, global.AsGradient);
    global.jqueryAsColorPickerEs = mod.exports;
  }
})(this, function(_jquery, _jqueryAsColor, _jqueryAsGradient) {
  'use strict';

  var _jquery2 = _interopRequireDefault(_jquery);

  var _jqueryAsColor2 = _interopRequireDefault(_jqueryAsColor);

  var _jqueryAsGradient2 = _interopRequireDefault(_jqueryAsGradient);

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule
      ? obj
      : {
          default: obj
        };
  }

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
    namespace: 'asColorPicker',
    readonly: false,
    skin: null,
    lang: 'en',
    hideInput: false,
    hideFireChange: true,
    keyboard: false,
    color: {
      format: false,
      alphaConvert: {
        // or false will disable convert
        RGB: 'RGBA',
        HSL: 'HSLA',
        HEX: 'RGBA',
        NAMESPACE: 'RGBA'
      },
      shortenHex: false,
      hexUseName: false,
      reduceAlpha: true,
      nameDegradation: 'HEX',
      invalidValue: '',
      zeroAlphaAsTransparent: true
    },
    mode: 'simple',
    onInit: null,
    onReady: null,
    onChange: null,
    onClose: null,
    onOpen: null,
    onApply: null
  };

  var MODES = {
    simple: {
      trigger: true,
      clear: true,
      saturation: true,
      hue: true,
      alpha: true
    },
    palettes: {
      trigger: true,
      clear: true,
      palettes: true
    },
    complex: {
      trigger: true,
      clear: true,
      preview: true,
      palettes: true,
      saturation: true,
      hue: true,
      alpha: true,
      hex: true,
      buttons: true
    },
    gradient: {
      trigger: true,
      clear: true,
      preview: true,
      palettes: true,
      saturation: true,
      hue: true,
      alpha: true,
      hex: true,
      gradient: true
    }
  };

  // alpha
  var alpha = {
    size: 150,

    defaults: {
      direction: 'vertical',
      template: function template(namespace) {
        return (
          '<div class="' +
          namespace +
          '-alpha ' +
          namespace +
          '-alpha-' +
          this.direction +
          '"><i></i></div>'
        );
      }
    },

    data: {},

    init: function init(api, options) {
      var that = this;

      this.options = $.extend(this.defaults, options);
      that.direction = this.options.direction;
      this.api = api;

      this.$alpha = $(this.options.template.call(that, api.namespace)).appendTo(
        api.$dropdown
      );
      this.$handle = this.$alpha.find('i');

      api.$element.on('asColorPicker::firstOpen', function() {
        // init variable
        if (that.direction === 'vertical') {
          that.size = that.$alpha.height();
        } else {
          that.size = that.$alpha.width();
        }
        that.step = that.size / 360;

        // bind events
        that.bindEvents();
        that.keyboard();
      });

      api.$element.on('asColorPicker::update asColorPicker::setup', function(
        e,
        api,
        color
      ) {
        that.update(color);
      });
    },

    bindEvents: function bindEvents() {
      var that = this;
      this.$alpha.on(this.api.eventName('mousedown'), function(e) {
        var rightclick = e.which ? e.which === 3 : e.button === 2;
        if (rightclick) {
          return false;
        }
        $.proxy(that.mousedown, that)(e);
      });
    },

    mousedown: function mousedown(e) {
      var offset = this.$alpha.offset();
      if (this.direction === 'vertical') {
        this.data.startY = e.pageY;
        this.data.top = e.pageY - offset.top;
        this.move(this.data.top);
      } else {
        this.data.startX = e.pageX;
        this.data.left = e.pageX - offset.left;
        this.move(this.data.left);
      }

      this.mousemove = function(e) {
        var position = void 0;
        if (this.direction === 'vertical') {
          position =
            this.data.top + (e.pageY || this.data.startY) - this.data.startY;
        } else {
          position =
            this.data.left + (e.pageX || this.data.startX) - this.data.startX;
        }

        this.move(position);
        return false;
      };

      this.mouseup = function() {
        $(document).off({
          mousemove: this.mousemove,
          mouseup: this.mouseup
        });
        if (this.direction === 'vertical') {
          this.data.top = this.data.cach;
        } else {
          this.data.left = this.data.cach;
        }

        return false;
      };

      $(document).on({
        mousemove: $.proxy(this.mousemove, this),
        mouseup: $.proxy(this.mouseup, this)
      });
      return false;
    },

    move: function move(position, alpha, update) {
      position = Math.max(0, Math.min(this.size, position));
      this.data.cach = position;
      if (typeof alpha === 'undefined') {
        alpha = 1 - position / this.size;
      }
      alpha = Math.max(0, Math.min(1, alpha));
      if (this.direction === 'vertical') {
        this.$handle.css({
          top: position
        });
      } else {
        this.$handle.css({
          left: position
        });
      }

      if (update !== false) {
        this.api.set({
          a: Math.round(alpha * 100) / 100
        });
      }
    },

    moveLeft: function moveLeft() {
      var step = this.step;
      var data = this.data;
      data.left = Math.max(0, Math.min(this.width, data.left - step));
      this.move(data.left);
    },

    moveRight: function moveRight() {
      var step = this.step;
      var data = this.data;
      data.left = Math.max(0, Math.min(this.width, data.left + step));
      this.move(data.left);
    },

    moveUp: function moveUp() {
      var step = this.step;
      var data = this.data;
      data.top = Math.max(0, Math.min(this.width, data.top - step));
      this.move(data.top);
    },

    moveDown: function moveDown() {
      var step = this.step;
      var data = this.data;
      data.top = Math.max(0, Math.min(this.width, data.top + step));
      this.move(data.top);
    },

    keyboard: function keyboard() {
      var keyboard = void 0;
      var that = this;
      if (this.api._keyboard) {
        keyboard = $.extend(true, {}, this.api._keyboard);
      } else {
        return false;
      }

      this.$alpha
        .attr('tabindex', '0')
        .on('focus', function() {
          if (this.direction === 'vertical') {
            keyboard.attach({
              up: function up() {
                that.moveUp();
              },
              down: function down() {
                that.moveDown();
              }
            });
          } else {
            keyboard.attach({
              left: function left() {
                that.moveLeft();
              },
              right: function right() {
                that.moveRight();
              }
            });
          }
          return false;
        })
        .on('blur', function() {
          keyboard.detach();
        });
    },

    update: function update(color) {
      var position = this.size * (1 - color.value.a);
      this.$alpha.css('backgroundColor', color.toHEX());

      this.move(position, color.value.a, false);
    },

    destroy: function destroy() {
      $(document).off({
        mousemove: this.mousemove,
        mouseup: this.mouseup
      });
    }
  };

  // hex
  var hex = {
    init: function init(api) {
      var template = '<input type="text" class="' + api.namespace + '-hex" />';
      this.$hex = $(template).appendTo(api.$dropdown);

      this.$hex.on('change', function() {
        api.set(this.value);
      });

      var that = this;
      api.$element.on('asColorPicker::update asColorPicker::setup', function(
        e,
        api,
        color
      ) {
        that.update(color);
      });
    },

    update: function update(color) {
      this.$hex.val(color.toHEX());
    }
  };

  // hue
  var hue = {
    size: 150,

    defaults: {
      direction: 'vertical',
      template: function template() {
        var namespace = this.api.namespace;
        return (
          '<div class="' +
          namespace +
          '-hue ' +
          namespace +
          '-hue-' +
          this.direction +
          '"><i></i></div>'
        );
      }
    },

    data: {},

    init: function init(api, options) {
      var that = this;

      this.options = $.extend(this.defaults, options);
      this.direction = this.options.direction;
      this.api = api;

      this.$hue = $(this.options.template.call(that)).appendTo(api.$dropdown);
      this.$handle = this.$hue.find('i');

      api.$element.on('asColorPicker::firstOpen', function() {
        // init variable
        if (that.direction === 'vertical') {
          that.size = that.$hue.height();
        } else {
          that.size = that.$hue.width();
        }
        that.step = that.size / 360;

        // bind events
        that.bindEvents(api);
        that.keyboard(api);
      });

      api.$element.on('asColorPicker::update asColorPicker::setup', function(
        e,
        api,
        color
      ) {
        that.update(color);
      });
    },

    bindEvents: function bindEvents() {
      var that = this;
      this.$hue.on(this.api.eventName('mousedown'), function(e) {
        var rightclick = e.which ? e.which === 3 : e.button === 2;
        if (rightclick) {
          return false;
        }
        $.proxy(that.mousedown, that)(e);
      });
    },

    mousedown: function mousedown(e) {
      var offset = this.$hue.offset();
      if (this.direction === 'vertical') {
        this.data.startY = e.pageY;
        this.data.top = e.pageY - offset.top;
        this.move(this.data.top);
      } else {
        this.data.startX = e.pageX;
        this.data.left = e.pageX - offset.left;
        this.move(this.data.left);
      }

      this.mousemove = function(e) {
        var position = void 0;
        if (this.direction === 'vertical') {
          position =
            this.data.top + (e.pageY || this.data.startY) - this.data.startY;
        } else {
          position =
            this.data.left + (e.pageX || this.data.startX) - this.data.startX;
        }

        this.move(position);
        return false;
      };

      this.mouseup = function() {
        $(document).off({
          mousemove: this.mousemove,
          mouseup: this.mouseup
        });
        if (this.direction === 'vertical') {
          this.data.top = this.data.cach;
        } else {
          this.data.left = this.data.cach;
        }

        return false;
      };

      $(document).on({
        mousemove: $.proxy(this.mousemove, this),
        mouseup: $.proxy(this.mouseup, this)
      });

      return false;
    },

    move: function move(position, hub, update) {
      position = Math.max(0, Math.min(this.size, position));
      this.data.cach = position;
      if (typeof hub === 'undefined') {
        hub = (1 - position / this.size) * 360;
      }
      hub = Math.max(0, Math.min(360, hub));
      if (this.direction === 'vertical') {
        this.$handle.css({
          top: position
        });
      } else {
        this.$handle.css({
          left: position
        });
      }
      if (update !== false) {
        this.api.set({
          h: hub
        });
      }
    },

    moveLeft: function moveLeft() {
      var step = this.step;
      var data = this.data;
      data.left = Math.max(0, Math.min(this.width, data.left - step));
      this.move(data.left);
    },

    moveRight: function moveRight() {
      var step = this.step;
      var data = this.data;
      data.left = Math.max(0, Math.min(this.width, data.left + step));
      this.move(data.left);
    },

    moveUp: function moveUp() {
      var step = this.step;
      var data = this.data;
      data.top = Math.max(0, Math.min(this.width, data.top - step));
      this.move(data.top);
    },

    moveDown: function moveDown() {
      var step = this.step;
      var data = this.data;
      data.top = Math.max(0, Math.min(this.width, data.top + step));
      this.move(data.top);
    },

    keyboard: function keyboard() {
      var keyboard = void 0;
      var that = this;
      if (this.api._keyboard) {
        keyboard = $.extend(true, {}, this.api._keyboard);
      } else {
        return false;
      }

      this.$hue
        .attr('tabindex', '0')
        .on('focus', function() {
          if (this.direction === 'vertical') {
            keyboard.attach({
              up: function up() {
                that.moveUp();
              },
              down: function down() {
                that.moveDown();
              }
            });
          } else {
            keyboard.attach({
              left: function left() {
                that.moveLeft();
              },
              right: function right() {
                that.moveRight();
              }
            });
          }
          return false;
        })
        .on('blur', function() {
          keyboard.detach();
        });
    },

    update: function update(color) {
      var position =
        color.value.h === 0 ? 0 : this.size * (1 - color.value.h / 360);
      this.move(position, color.value.h, false);
    },

    destroy: function destroy() {
      $(document).off({
        mousemove: this.mousemove,
        mouseup: this.mouseup
      });
    }
  };

  // saturation
  var saturation = {
    defaults: {
      template: function template(namespace) {
        return '<div class="' + namespace + '-saturation"><i><b></b></i></div>';
      }
    },

    width: 0,
    height: 0,
    size: 6,
    data: {},

    init: function init(api, options) {
      var that = this;
      this.options = $.extend(this.defaults, options);
      this.api = api;

      //build element and add component to picker
      this.$saturation = $(
        this.options.template.call(that, api.namespace)
      ).appendTo(api.$dropdown);
      this.$handle = this.$saturation.find('i');

      api.$element.on('asColorPicker::firstOpen', function() {
        // init variable
        that.width = that.$saturation.width();
        that.height = that.$saturation.height();
        that.step = {
          left: that.width / 20,
          top: that.height / 20
        };
        that.size = that.$handle.width() / 2;

        // bind events
        that.bindEvents();
        that.keyboard(api);
      });

      api.$element.on('asColorPicker::update asColorPicker::setup', function(
        e,
        api,
        color
      ) {
        that.update(color);
      });
    },

    bindEvents: function bindEvents() {
      var that = this;

      this.$saturation.on(this.api.eventName('mousedown'), function(e) {
        var rightclick = e.which ? e.which === 3 : e.button === 2;
        if (rightclick) {
          return false;
        }
        that.mousedown(e);
      });
    },

    mousedown: function mousedown(e) {
      var offset = this.$saturation.offset();

      this.data.startY = e.pageY;
      this.data.startX = e.pageX;
      this.data.top = e.pageY - offset.top;
      this.data.left = e.pageX - offset.left;
      this.data.cach = {};

      this.move(this.data.left, this.data.top);

      this.mousemove = function(e) {
        var x =
          this.data.left + (e.pageX || this.data.startX) - this.data.startX;
        var y =
          this.data.top + (e.pageY || this.data.startY) - this.data.startY;
        this.move(x, y);
        return false;
      };

      this.mouseup = function() {
        $(document).off({
          mousemove: this.mousemove,
          mouseup: this.mouseup
        });
        this.data.left = this.data.cach.left;
        this.data.top = this.data.cach.top;

        return false;
      };

      $(document).on({
        mousemove: $.proxy(this.mousemove, this),
        mouseup: $.proxy(this.mouseup, this)
      });

      return false;
    },

    move: function move(x, y, update) {
      y = Math.max(0, Math.min(this.height, y));
      x = Math.max(0, Math.min(this.width, x));

      if (this.data.cach === undefined) {
        this.data.cach = {};
      }
      this.data.cach.left = x;
      this.data.cach.top = y;

      this.$handle.css({
        top: y - this.size,
        left: x - this.size
      });

      if (update !== false) {
        this.api.set({
          s: x / this.width,
          v: 1 - y / this.height
        });
      }
    },

    update: function update(color) {
      if (color.value.h === undefined) {
        color.value.h = 0;
      }
      this.$saturation.css(
        'backgroundColor',
        _jqueryAsColor2.default.HSLtoHEX({
          h: color.value.h,
          s: 1,
          l: 0.5
        })
      );

      var x = color.value.s * this.width;
      var y = (1 - color.value.v) * this.height;

      this.move(x, y, false);
    },

    moveLeft: function moveLeft() {
      var step = this.step.left;
      var data = this.data;
      data.left = Math.max(0, Math.min(this.width, data.left - step));
      this.move(data.left, data.top);
    },

    moveRight: function moveRight() {
      var step = this.step.left;
      var data = this.data;
      data.left = Math.max(0, Math.min(this.width, data.left + step));
      this.move(data.left, data.top);
    },

    moveUp: function moveUp() {
      var step = this.step.top;
      var data = this.data;
      data.top = Math.max(0, Math.min(this.width, data.top - step));
      this.move(data.left, data.top);
    },

    moveDown: function moveDown() {
      var step = this.step.top;
      var data = this.data;
      data.top = Math.max(0, Math.min(this.width, data.top + step));
      this.move(data.left, data.top);
    },

    keyboard: function keyboard() {
      var keyboard = void 0;
      var that = this;
      if (this.api._keyboard) {
        keyboard = $.extend(true, {}, this.api._keyboard);
      } else {
        return false;
      }

      this.$saturation
        .attr('tabindex', '0')
        .on('focus', function() {
          keyboard.attach({
            left: function left() {
              that.moveLeft();
            },
            right: function right() {
              that.moveRight();
            },
            up: function up() {
              that.moveUp();
            },
            down: function down() {
              that.moveDown();
            }
          });
          return false;
        })
        .on('blur', function() {
          keyboard.detach();
        });
    },

    destroy: function destroy() {
      $(document).off({
        mousemove: this.mousemove,
        mouseup: this.mouseup
      });
    }
  };

  // buttons
  var buttons = {
    defaults: {
      apply: false,
      cancel: true,
      applyText: null,
      cancelText: null,
      template: function template(namespace) {
        return '<div class="' + namespace + '-buttons"></div>';
      },
      applyTemplate: function applyTemplate(namespace) {
        return (
          '<a href="#" alt="' +
          this.options.applyText +
          '" class="' +
          namespace +
          '-buttons-apply">' +
          this.options.applyText +
          '</a>'
        );
      },
      cancelTemplate: function cancelTemplate(namespace) {
        return (
          '<a href="#" alt="' +
          this.options.cancelText +
          '" class="' +
          namespace +
          '-buttons-apply">' +
          this.options.cancelText +
          '</a>'
        );
      }
    },

    init: function init(api, options) {
      var that = this;

      this.options = $.extend(
        this.defaults,
        {
          applyText: api.getString('applyText', 'apply'),
          cancelText: api.getString('cancelText', 'cancel')
        },
        options
      );
      this.$buttons = $(
        this.options.template.call(this, api.namespace)
      ).appendTo(api.$dropdown);

      api.$element.on('asColorPicker::firstOpen', function() {
        if (that.options.apply) {
          that.$apply = $(that.options.applyTemplate.call(that, api.namespace))
            .appendTo(that.$buttons)
            .on('click', function() {
              api.apply();
              return false;
            });
        }

        if (that.options.cancel) {
          that.$cancel = $(
            that.options.cancelTemplate.call(that, api.namespace)
          )
            .appendTo(that.$buttons)
            .on('click', function() {
              api.cancel();
              return false;
            });
        }
      });
    }
  };

  // trigger
  var trigger = {
    defaults: {
      template: function template(namespace) {
        return '<div class="' + namespace + '-trigger"><span></span></div>';
      }
    },

    init: function init(api, options) {
      this.options = $.extend(this.defaults, options);
      api.$trigger = $(this.options.template.call(this, api.namespace));
      this.$triggerInner = api.$trigger.children('span');

      api.$trigger.insertAfter(api.$element);
      api.$trigger.on('click', function() {
        if (!api.opened) {
          api.open();
        } else {
          api.close();
        }
        return false;
      });
      var that = this;
      api.$element.on('asColorPicker::update', function(
        e,
        api,
        color,
        gradient
      ) {
        if (typeof gradient === 'undefined') {
          gradient = false;
        }
        that.update(color, gradient);
      });

      this.update(api.color);
    },

    update: function update(color, gradient) {
      if (gradient) {
        this.$triggerInner.css('background', gradient.toString(true));
      } else {
        this.$triggerInner.css('background', color.toRGBA());
      }
    },

    destroy: function destroy(api) {
      api.$trigger.remove();
    }
  };

  // clear
  var clear = {
    defaults: {
      template: function template(namespace) {
        return '<a href="#" class="' + namespace + '-clear"></a>';
      }
    },

    init: function init(api, options) {
      if (api.options.hideInput) {
        return;
      }
      this.options = $.extend(this.defaults, options);
      this.$clear = $(
        this.options.template.call(this, api.namespace)
      ).insertAfter(api.$element);

      this.$clear.on('click', function() {
        api.clear();
        return false;
      });
    }
  };

  // info
  var info = {
    color: ['white', 'black', 'transparent'],

    init: function init(api) {
      var template =
        '<ul class="' +
        api.namespace +
        '-info"><li><label>R:<input type="text" data-type="r"/></label></li><li><label>G:<input type="text" data-type="g"/></label></li><li><label>B:<input type="text" data-type="b"/></label></li><li><label>A:<input type="text" data-type="a"/></label></li></ul>';
      this.$info = $(template).appendTo(api.$dropdown);
      this.$r = this.$info.find('[data-type="r"]');
      this.$g = this.$info.find('[data-type="g"]');
      this.$b = this.$info.find('[data-type="b"]');
      this.$a = this.$info.find('[data-type="a"]');

      this.$info.on(api.eventName('keyup update change'), 'input', function(e) {
        var val = void 0;
        var type = $(e.target).data('type');
        switch (type) {
          case 'r':
          case 'g':
          case 'b':
            val = parseInt(this.value, 10);
            if (val > 255) {
              val = 255;
            } else if (val < 0) {
              val = 0;
            }
            break;
          case 'a':
            val = parseFloat(this.value, 10);
            if (val > 1) {
              val = 1;
            } else if (val < 0) {
              val = 0;
            }
            break;
          default:
            break;
        }
        if (isNaN(val)) {
          val = 0;
        }
        var color = {};
        color[type] = val;
        api.set(color);
      });

      var that = this;
      api.$element.on('asColorPicker::update asColorPicker::setup', function(
        e,
        color
      ) {
        that.update(color);
      });
    },

    update: function update(color) {
      this.$r.val(color.value.r);
      this.$g.val(color.value.g);
      this.$b.val(color.value.b);
      this.$a.val(color.value.a);
    }
  };

  // palettes
  function noop() {
    return;
  }
  if (!window.localStorage) {
    window.localStorage = noop;
  }

  var palettes = {
    defaults: {
      template: function template(namespace) {
        return '<ul class="' + namespace + '-palettes"></ul>';
      },
      item: function item(namespace, color) {
        return (
          '<li data-color="' +
          color +
          '"><span style="background-color:' +
          color +
          '" /></li>'
        );
      },

      colors: ['white', 'black', 'red', 'blue', 'yellow'],
      max: 10,
      localStorage: true
    },

    init: function init(api, options) {
      var that = this;
      var colors = void 0;
      var asColor = (0, _jqueryAsColor2.default)();

      this.options = $.extend(true, {}, this.defaults, options);
      this.colors = [];
      var localKey = void 0;

      if (this.options.localStorage) {
        localKey = api.namespace + '_palettes_' + api.id;
        colors = this.getLocal(localKey);
        if (!colors) {
          colors = this.options.colors;
          this.setLocal(localKey, colors);
        }
      } else {
        colors = this.options.colors;
      }

      for (var i in colors) {
        if (Object.hasOwnProperty.call(colors, i)) {
          this.colors.push(asColor.val(colors[i]).toRGBA());
        }
      }

      var list = '';
      $.each(this.colors, function(i, color) {
        list += that.options.item(api.namespace, color);
      });

      this.$palettes = $(this.options.template.call(this, api.namespace))
        .html(list)
        .appendTo(api.$dropdown);

      this.$palettes.on(api.eventName('click'), 'li', function(e) {
        var color = $(this).data('color');
        api.set(color);

        e.preventDefault();
        e.stopPropagation();
      });

      api.$element.on('asColorPicker::apply', function(e, api, color) {
        if (typeof color.toRGBA !== 'function') {
          color = color.get().color;
        }

        var rgba = color.toRGBA();
        if ($.inArray(rgba, that.colors) === -1) {
          if (that.colors.length >= that.options.max) {
            that.colors.shift();
            that.$palettes
              .find('li')
              .eq(0)
              .remove();
          }

          that.colors.push(rgba);

          that.$palettes.append(that.options.item(api.namespace, color));

          if (that.options.localStorage) {
            that.setLocal(localKey, that.colors);
          }
        }
      });
    },

    setLocal: function setLocal(key, value) {
      var jsonValue = JSON.stringify(value);

      localStorage[key] = jsonValue;
    },

    getLocal: function getLocal(key) {
      var value = localStorage[key];

      return value ? JSON.parse(value) : value;
    }
  };

  // preview
  var preview = {
    defaults: {
      template: function template(namespace) {
        return (
          '<ul class="' +
          namespace +
          '-preview"><li class="' +
          namespace +
          '-preview-current"><span /></li><li class="' +
          namespace +
          '-preview-previous"><span /></li></ul>'
        );
      }
    },

    init: function init(api, options) {
      var that = this;
      this.options = $.extend(this.defaults, options);
      this.$preview = $(
        this.options.template.call(that, api.namespace)
      ).appendTo(api.$dropdown);
      this.$current = this.$preview.find(
        '.' + api.namespace + '-preview-current span'
      );
      this.$previous = this.$preview.find(
        '.' + api.namespace + '-preview-previous span'
      );

      api.$element.on('asColorPicker::firstOpen', function() {
        that.$previous.on('click', function() {
          api.set($(this).data('color'));
          return false;
        });
      });

      api.$element.on('asColorPicker::setup', function(e, api, color) {
        that.updateCurrent(color);
        that.updatePreview(color);
      });
      api.$element.on('asColorPicker::update', function(e, api, color) {
        that.updateCurrent(color);
      });
    },

    updateCurrent: function updateCurrent(color) {
      this.$current.css('backgroundColor', color.toRGBA());
    },

    updatePreview: function updatePreview(color) {
      this.$previous.css('backgroundColor', color.toRGBA());
      this.$previous.data('color', {
        r: color.value.r,
        g: color.value.g,
        b: color.value.b,
        a: color.value.a
      });
    }
  };

  // gradient
  function conventToPercentage(n) {
    if (n < 0) {
      n = 0;
    } else if (n > 1) {
      n = 1;
    }
    return n * 100 + '%';
  }

  var Gradient = function Gradient(api, options) {
    this.api = api;
    this.options = options;
    this.classes = {
      enable: api.namespace + '-gradient_enable',
      marker: api.namespace + '-gradient-marker',
      active: api.namespace + '-gradient-marker_active',
      focus: api.namespace + '-gradient_focus'
    };
    this.isEnabled = false;
    this.initialized = false;
    this.current = null;
    this.value = (0, _jqueryAsGradient2.default)(this.options.settings);
    this.$doc = $(document);

    var that = this;
    $.extend(that, {
      init: function init() {
        that.$wrap = $(that.options.template.call(that)).appendTo(
          api.$dropdown
        );

        that.$gradient = that.$wrap.filter('.' + api.namespace + '-gradient');

        this.angle.init();
        this.preview.init();
        this.markers.init();
        this.wheel.init();

        this.bind();

        if (
          that.options.switchable === false ||
          this.value.matchString(api.element.value)
        ) {
          that.enable();
        }
        this.initialized = true;
      },
      bind: function bind() {
        var namespace = api.namespace;

        that.$gradient.on('update', function() {
          var current = that.value.getById(that.current);

          if (current) {
            api._trigger('update', current.color, that.value);
          }

          if (api.element.value !== that.value.toString()) {
            api._updateInput();
          }
        });

        // that.$gradient.on('add', function(e, data) {
        //   if (data.stop) {
        //     that.active(data.stop.id);
        //     api._trigger('update', data.stop.color, that.value);
        //     api._updateInput();
        //   }
        // });

        if (that.options.switchable) {
          that.$wrap.on(
            'click',
            '.' + namespace + '-gradient-switch',
            function() {
              if (that.isEnabled) {
                that.disable();
              } else {
                that.enable();
              }

              return false;
            }
          );
        }

        that.$wrap.on(
          'click',
          '.' + namespace + '-gradient-cancel',
          function() {
            if (
              that.options.switchable === false ||
              _jqueryAsGradient2.default.matchString(api.originValue)
            ) {
              that.overrideCore();
            }

            api.cancel();

            return false;
          }
        );
      },
      overrideCore: function overrideCore() {
        api.set = function(value) {
          if (value !== '') {
            api.isEmpty = false;
          } else {
            api.isEmpty = true;
          }
          if (typeof value === 'string') {
            if (
              that.options.switchable === false ||
              _jqueryAsGradient2.default.matchString(value)
            ) {
              if (that.isEnabled) {
                that.val(value);
                api.color = that.value;
                that.$gradient.trigger('update', that.value.value);
              } else {
                that.enable(value);
              }
            } else {
              that.disable();
              api.val(value);
            }
          } else {
            var current = that.value.getById(that.current);

            if (current) {
              current.color.val(value);
              api._trigger('update', current.color, that.value);
            }

            that.$gradient.trigger('update', {
              id: that.current,
              stop: current
            });
          }
        };

        api._setup = function() {
          var current = that.value.getById(that.current);

          api._trigger('setup', current.color);
        };
      },
      revertCore: function revertCore() {
        api.set = $.proxy(api._set, api);
        api._setup = function() {
          api._trigger('setup', api.color);
        };
      },

      preview: {
        init: function init() {
          var _this = this;

          that.$preview = that.$gradient.find(
            '.' + api.namespace + '-gradient-preview'
          );

          that.$gradient.on('add del update empty', function() {
            _this.render();
          });
        },
        render: function render() {
          that.$preview.css({
            'background-image': that.value.toStringWithAngle('to right', true)
          });
          that.$preview.css({
            'background-image': that.value.toStringWithAngle('to right')
          });
        }
      },
      markers: {
        width: 160,
        init: function init() {
          var _this2 = this;

          that.$markers = that.$gradient
            .find('.' + api.namespace + '-gradient-markers')
            .attr('tabindex', 0);

          that.$gradient.on('add', function(e, data) {
            _this2.add(data.stop);
          });

          that.$gradient.on('active', function(e, data) {
            _this2.active(data.id);
          });

          that.$gradient.on('del', function(e, data) {
            _this2.del(data.id);
          });

          that.$gradient.on('update', function(e, data) {
            if (data.stop) {
              _this2.update(data.stop.id, data.stop.color);
            }
          });

          that.$gradient.on('empty', function() {
            _this2.empty();
          });

          that.$markers.on(that.api.eventName('mousedown'), function(e) {
            var rightclick = e.which ? e.which === 3 : e.button === 2;
            if (rightclick) {
              return false;
            }

            var position = parseFloat(
              (e.pageX - that.$markers.offset().left) / that.markers.width,
              10
            );
            that.add('#fff', position);
            return false;
          });

          /* eslint consistent-this: "off" */
          var self = this;
          that.$markers.on(that.api.eventName('mousedown'), 'li', function(e) {
            var rightclick = e.which ? e.which === 3 : e.button === 2;
            if (rightclick) {
              return false;
            }
            self.mousedown(this, e);
            return false;
          });

          that.$doc.on(that.api.eventName('keydown'), function(e) {
            if (that.api.opened && that.$markers.is('.' + that.classes.focus)) {
              var key = e.keyCode || e.which;
              if (key === 46 || key === 8) {
                if (that.value.length <= 2) {
                  return false;
                }

                that.del(that.current);

                return false;
              }
            }
          });

          that.$markers
            .on(that.api.eventName('focus'), function() {
              that.$markers.addClass(that.classes.focus);
            })
            .on(that.api.eventName('blur'), function() {
              that.$markers.removeClass(that.classes.focus);
            });

          that.$markers.on(that.api.eventName('click'), 'li', function() {
            var id = $(this).data('id');
            that.active(id);
          });
        },
        getMarker: function getMarker(id) {
          return that.$markers.find('[data-id="' + id + '"]');
        },
        update: function update(id, color) {
          var $marker = this.getMarker(id);
          $marker.find('span').css('background-color', color.toHEX());
          $marker.find('i').css('background-color', color.toHEX());
        },
        add: function add(stop) {
          $(
            '<li data-id="' +
              stop.id +
              '" style="left:' +
              conventToPercentage(stop.position) +
              '" class="' +
              that.classes.marker +
              '"><span style="background-color: ' +
              stop.color.toHEX() +
              '"></span><i style="background-color: ' +
              stop.color.toHEX() +
              '"></i></li>'
          ).appendTo(that.$markers);
        },
        empty: function empty() {
          that.$markers.html('');
        },
        del: function del(id) {
          var $marker = this.getMarker(id);
          var $to = $marker.prev();
          if ($to.length === 0) {
            $to = $marker.next();
          }

          that.active($to.data('id'));
          $marker.remove();
        },
        active: function active(id) {
          that.$markers.children().removeClass(that.classes.active);

          var $marker = this.getMarker(id);
          $marker.addClass(that.classes.active);

          that.$markers.focus();
          // that.api._trigger('apply', that.value.getById(id).color);
        },
        mousedown: function mousedown(marker, e) {
          var self = this;
          /* eslint consistent-this: "off" */
          var id = $(marker).data('id');
          var first = $(marker).position().left;
          var start = e.pageX;
          var end = void 0;

          this.mousemove = function(e) {
            end = e.pageX || start;
            var position = (first + end - start) / this.width;
            self.move(marker, position, id);
            return false;
          };

          this.mouseup = function() {
            $(document).off({
              mousemove: this.mousemove,
              mouseup: this.mouseup
            });

            return false;
          };

          that.$doc.on({
            mousemove: $.proxy(this.mousemove, this),
            mouseup: $.proxy(this.mouseup, this)
          });
          that.active(id);
          return false;
        },
        move: function move(marker, position, id) {
          that.api.isEmpty = false;
          position = Math.max(0, Math.min(1, position));
          $(marker).css({
            left: conventToPercentage(position)
          });
          if (!id) {
            id = $(marker).data('id');
          }

          that.value.getById(id).setPosition(position);

          that.$gradient.trigger('update', {
            id: $(marker).data('id'),
            position: position
          });
        }
      },
      wheel: {
        init: function init() {
          var _this3 = this;

          that.$wheel = that.$gradient.find(
            '.' + api.namespace + '-gradient-wheel'
          );
          that.$pointer = that.$wheel.find('i');

          that.$gradient.on('update', function(e, data) {
            if (typeof data.angle !== 'undefined') {
              _this3.position(data.angle);
            }
          });

          that.$wheel.on(that.api.eventName('mousedown'), function(e) {
            var rightclick = e.which ? e.which === 3 : e.button === 2;
            if (rightclick) {
              return false;
            }
            _this3.mousedown(e, that);
            return false;
          });
        },
        mousedown: function mousedown(e, that) {
          var _this4 = this;

          var offset = that.$wheel.offset();
          var r = that.$wheel.width() / 2;
          var startX = offset.left + r;
          var startY = offset.top + r;
          var $doc = that.$doc;

          this.r = r;

          this.wheelMove = function(e) {
            var x = e.pageX - startX;
            var y = startY - e.pageY;

            var position = _this4.getPosition(x, y);
            var angle = _this4.calAngle(position.x, position.y);
            that.api.isEmpty = false;
            that.setAngle(angle);
          };
          this.wheelMouseup = function() {
            $doc.off({
              mousemove: this.wheelMove,
              mouseup: this.wheelMouseup
            });
            return false;
          };
          $doc.on({
            mousemove: $.proxy(this.wheelMove, this),
            mouseup: $.proxy(this.wheelMouseup, this)
          });

          this.wheelMove(e);
        },
        getPosition: function getPosition(a, b) {
          var r = this.r;
          var x = a / Math.sqrt(a * a + b * b) * r;
          var y = b / Math.sqrt(a * a + b * b) * r;
          return {
            x: x,
            y: y
          };
        },
        calAngle: function calAngle(x, y) {
          var deg = Math.round(Math.atan(Math.abs(x / y)) * (180 / Math.PI));
          if (x < 0 && y > 0) {
            return 360 - deg;
          }
          if (x < 0 && y <= 0) {
            return deg + 180;
          }
          if (x >= 0 && y <= 0) {
            return 180 - deg;
          }
          if (x >= 0 && y > 0) {
            return deg;
          }
        },
        set: function set(value) {
          that.value.angle(value);
          that.$gradient.trigger('update', {
            angle: value
          });
        },
        position: function position(angle) {
          var r = this.r || that.$wheel.width() / 2;
          var pos = this.calPointer(angle, r);
          that.$pointer.css({
            left: pos.x,
            top: pos.y
          });
        },
        calPointer: function calPointer(angle, r) {
          var x = Math.sin(angle * Math.PI / 180) * r;
          var y = Math.cos(angle * Math.PI / 180) * r;
          return {
            x: r + x,
            y: r - y
          };
        }
      },
      angle: {
        init: function init() {
          that.$angle = that.$gradient.find(
            '.' + api.namespace + '-gradient-angle'
          );

          that.$angle
            .on(that.api.eventName('blur'), function() {
              that.setAngle(this.value);
              return false;
            })
            .on(that.api.eventName('keydown'), function(e) {
              var key = e.keyCode || e.which;
              if (key === 13) {
                that.api.isEmpty = false;
                $(this).blur();
                return false;
              }
            });

          that.$gradient.on('update', function(e, data) {
            if (typeof data.angle !== 'undefined') {
              that.$angle.val(data.angle);
            }
          });
        },
        set: function set(value) {
          that.value.angle(value);
          that.$gradient.trigger('update', {
            angle: value
          });
        }
      }
    });

    this.init();
  };

  Gradient.prototype = {
    constructor: Gradient,

    enable: function enable(value) {
      if (this.isEnabled === true) {
        return;
      }
      this.isEnabled = true;
      this.overrideCore();

      this.$gradient.addClass(this.classes.enable);
      this.markers.width = this.$markers.width();

      if (typeof value === 'undefined') {
        value = this.api.element.value;
      }

      if (value !== '') {
        this.api.isEmpty = false;
      } else {
        this.api.isEmpty = true;
      }

      if (!_jqueryAsGradient2.default.matchString(value) && this._last) {
        this.value = this._last;
      } else {
        this.val(value);
      }
      this.api.color = this.value;

      this.$gradient.trigger('update', this.value.value);

      if (this.api.opened) {
        this.api.position();
      }
    },
    val: function val(string) {
      if (string !== '' && this.value.toString() === string) {
        return;
      }
      this.empty();
      this.value.val(string);
      this.value.reorder();

      if (this.value.length < 2) {
        var fill = string;

        if (!_jqueryAsColor2.default.matchString(string)) {
          fill = 'rgba(0,0,0,1)';
        }

        if (this.value.length === 0) {
          this.value.append(fill, 0);
        }
        if (this.value.length === 1) {
          this.value.append(fill, 1);
        }
      }

      var stop = void 0;
      for (var i = 0; i < this.value.length; i++) {
        stop = this.value.get(i);
        if (stop) {
          this.$gradient.trigger('add', {
            stop: stop
          });
        }
      }

      this.active(stop.id);
    },
    disable: function disable() {
      if (this.isEnabled === false) {
        return;
      }
      this.isEnabled = false;
      this.revertCore();

      this.$gradient.removeClass(this.classes.enable);
      this._last = this.value;
      this.api.color = this.api.color.getCurrent().color;
      this.api.set(this.api.color.value);

      if (this.api.opened) {
        this.api.position();
      }
    },
    active: function active(id) {
      if (this.current !== id) {
        this.current = id;
        this.value.setCurrentById(id);

        this.$gradient.trigger('active', {
          id: id
        });
      }
    },
    empty: function empty() {
      this.value.empty();
      this.$gradient.trigger('empty');
    },
    add: function add(color, position) {
      var stop = this.value.insert(color, position);
      this.api.isEmpty = false;
      this.value.reorder();

      this.$gradient.trigger('add', {
        stop: stop
      });

      this.active(stop.id);

      this.$gradient.trigger('update', {
        stop: stop
      });
      return stop;
    },
    del: function del(id) {
      if (this.value.length <= 2) {
        return;
      }
      this.value.removeById(id);
      this.value.reorder();
      this.$gradient.trigger('del', {
        id: id
      });

      this.$gradient.trigger('update', {});
    },
    setAngle: function setAngle(value) {
      this.value.angle(value);
      this.$gradient.trigger('update', {
        angle: value
      });
    }
  };

  var gradient = {
    defaults: {
      switchable: true,
      switchText: 'Gradient',
      cancelText: 'Cancel',
      settings: {
        forceStandard: true,
        angleUseKeyword: true,
        emptyString: '',
        degradationFormat: false,
        cleanPosition: false,
        color: {
          format: 'rgb' // rgb, rgba, hsl, hsla, hex
        }
      },
      template: function template() {
        var namespace = this.api.namespace;
        var control = '<div class="' + namespace + '-gradient-control">';
        if (this.options.switchable) {
          control +=
            '<a href="#" class="' +
            namespace +
            '-gradient-switch">' +
            this.options.switchText +
            '</a>';
        }
        control +=
          '<a href="#" class="' +
          namespace +
          '-gradient-cancel">' +
          this.options.cancelText +
          '</a></div>';

        return (
          control +
          '<div class="' +
          namespace +
          '-gradient"><div class="' +
          namespace +
          '-gradient-preview"><ul class="' +
          namespace +
          '-gradient-markers"></ul></div><div class="' +
          namespace +
          '-gradient-wheel"><i></i></div><input class="' +
          namespace +
          '-gradient-angle" type="text" value="" size="3" /></div>'
        );
      }
    },

    init: function init(api, options) {
      var that = this;

      api.$element.on('asColorPicker::ready', function(event, instance) {
        if (instance.options.mode !== 'gradient') {
          return;
        }

        that.defaults.settings.color = api.options.color;
        options = $.extend(true, that.defaults, options);

        api.gradient = new Gradient(api, options);
      });
    }
  };

  var NAMESPACE$1 = 'asColorPicker';
  var COMPONENTS = {};
  var LOCALIZATIONS = {
    en: {
      cancelText: 'cancel',
      applyText: 'apply'
    }
  };

  var id = 0;

  function createId(api) {
    api.id = id;
    id++;
  }

  var AsColorPicker = (function() {
    function AsColorPicker(element, options) {
      _classCallCheck(this, AsColorPicker);

      this.element = element;
      this.$element = (0, _jquery2.default)(element);

      //flag
      this.opened = false;
      this.firstOpen = true;
      this.disabled = false;
      this.initialed = false;
      this.originValue = this.element.value;
      this.isEmpty = false;

      createId(this);

      this.options = _jquery2.default.extend(
        true,
        {},
        DEFAULTS,
        options,
        this.$element.data()
      );
      this.namespace = this.options.namespace;

      this.classes = {
        wrap: this.namespace + '-wrap',
        dropdown: this.namespace + '-dropdown',
        input: this.namespace + '-input',
        skin: this.namespace + '_' + this.options.skin,
        open: this.namespace + '_open',
        mask: this.namespace + '-mask',
        hideInput: this.namespace + '_hideInput',
        disabled: this.namespace + '_disabled',
        mode: this.namespace + '-mode_' + this.options.mode
      };

      if (this.options.hideInput) {
        this.$element.addClass(this.classes.hideInput);
      }

      this.components = MODES[this.options.mode];
      this._components = _jquery2.default.extend(true, {}, COMPONENTS);

      this._trigger('init');
      this.init();
    }

    _createClass(
      AsColorPicker,
      [
        {
          key: '_trigger',
          value: function _trigger(eventType) {
            for (
              var _len = arguments.length,
                params = Array(_len > 1 ? _len - 1 : 0),
                _key = 1;
              _key < _len;
              _key++
            ) {
              params[_key - 1] = arguments[_key];
            }

            var data = [this].concat(params);

            // event
            this.$element.trigger(NAMESPACE$1 + '::' + eventType, data);

            // callback
            eventType = eventType.replace(/\b\w+\b/g, function(word) {
              return word.substring(0, 1).toUpperCase() + word.substring(1);
            });
            var onFunction = 'on' + eventType;

            if (typeof this.options[onFunction] === 'function') {
              this.options[onFunction].apply(this, params);
            }
          }
        },
        {
          key: 'eventName',
          value: function eventName(events) {
            if (typeof events !== 'string' || events === '') {
              return '.' + this.options.namespace;
            }
            events = events.split(' ');

            var length = events.length;
            for (var i = 0; i < length; i++) {
              events[i] = events[i] + '.' + this.options.namespace;
            }
            return events.join(' ');
          }
        },
        {
          key: 'init',
          value: function init() {
            this.color = (0, _jqueryAsColor2.default)(
              this.element.value,
              this.options.color
            );

            this._create();

            if (this.options.skin) {
              this.$dropdown.addClass(this.classes.skin);
              this.$element.parent().addClass(this.classes.skin);
            }

            if (this.options.readonly) {
              this.$element.prop('readonly', true);
            }

            this._bindEvent();

            this.initialed = true;
            this._trigger('ready');
          }
        },
        {
          key: '_create',
          value: function _create() {
            var _this5 = this;

            this.$dropdown = (0, _jquery2.default)(
              '<div class="' +
                this.classes.dropdown +
                '" data-mode="' +
                this.options.mode +
                '"></div>'
            );
            this.$element
              .wrap('<div class="' + this.classes.wrap + '"></div>')
              .addClass(this.classes.input);

            this.$wrap = this.$element.parent();
            this.$body = (0, _jquery2.default)('body');

            this.$dropdown.data(NAMESPACE$1, this);

            var component = void 0;
            _jquery2.default.each(this.components, function(key, options) {
              if (options === true) {
                options = {};
              }
              if (_this5.options[key] !== undefined) {
                options = _jquery2.default.extend(
                  true,
                  {},
                  options,
                  _this5.options[key]
                );
              }
              if (Object.hasOwnProperty.call(_this5._components, key)) {
                component = _this5._components[key];
                component.init(_this5, options);
              }
            });

            this._trigger('create');
          }
        },
        {
          key: '_bindEvent',
          value: function _bindEvent() {
            var _this6 = this;

            this.$element.on(this.eventName('click'), function() {
              if (!_this6.opened) {
                _this6.open();
              }
              return false;
            });

            this.$element.on(this.eventName('keydown'), function(e) {
              if (e.keyCode === 9) {
                _this6.close();
              } else if (e.keyCode === 13) {
                _this6.val(_this6.element.value);
                _this6.close();
              }
            });

            this.$element.on(this.eventName('keyup'), function() {
              if (_this6.color.matchString(_this6.element.value)) {
                _this6.val(_this6.element.value);
              }
            });
          }
        },
        {
          key: 'opacity',
          value: function opacity(v) {
            if (v) {
              this.color.alpha(v);
            } else {
              return this.color.alpha();
            }
          }
        },
        {
          key: 'position',
          value: function position() {
            var hidden = !this.$element.is(':visible');
            var offset = hidden
              ? this.$trigger.offset()
              : this.$element.offset();
            var height = hidden
              ? this.$trigger.outerHeight()
              : this.$element.outerHeight();
            var width = hidden
              ? this.$trigger.outerWidth()
              : this.$element.outerWidth() + this.$trigger.outerWidth();
            var pickerWidth = this.$dropdown.outerWidth(true);
            var pickerHeight = this.$dropdown.outerHeight(true);
            var top = void 0;
            var left = void 0;

            if (
              pickerHeight + offset.top >
              (0, _jquery2.default)(window).height() +
                (0, _jquery2.default)(window).scrollTop()
            ) {
              top = offset.top - pickerHeight;
            } else {
              top = offset.top + height;
            }

            if (
              pickerWidth + offset.left >
              (0, _jquery2.default)(window).width() +
                (0, _jquery2.default)(window).scrollLeft()
            ) {
              left = offset.left - pickerWidth + width;
            } else {
              left = offset.left;
            }

            this.$dropdown.css({
              position: 'absolute',
              top: top,
              left: left
            });
          }
        },
        {
          key: 'open',
          value: function open() {
            if (this.disabled) {
              return;
            }
            this.originValue = this.element.value;

            if (this.$dropdown[0] !== this.$body.children().last()[0]) {
              this.$dropdown.detach().appendTo(this.$body);
            }

            this.$mask = (0, _jquery2.default)('.' + this.classes.mask);
            if (this.$mask.length === 0) {
              this.createMask();
            }

            // ensure the mask is always right before the dropdown
            if (this.$dropdown.prev()[0] !== this.$mask[0]) {
              this.$dropdown.before(this.$mask);
            }

            (0, _jquery2.default)('#asColorPicker-dropdown').removeAttr('id');
            this.$dropdown.attr('id', 'asColorPicker-dropdown');

            // show the mask
            this.$mask.show();

            this.position();

            (0, _jquery2.default)(window).on(
              this.eventName('resize'),
              _jquery2.default.proxy(this.position, this)
            );

            this.$dropdown.addClass(this.classes.open);

            this.opened = true;

            if (this.firstOpen) {
              this.firstOpen = false;
              this._trigger('firstOpen');
            }
            this._setup();
            this._trigger('open');
          }
        },
        {
          key: 'createMask',
          value: function createMask() {
            this.$mask = (0, _jquery2.default)(document.createElement('div'));
            this.$mask.attr('class', this.classes.mask);
            this.$mask.hide();
            this.$mask.appendTo(this.$body);

            this.$mask.on(
              this.eventName('mousedown touchstart click'),
              function(e) {
                var $dropdown = (0, _jquery2.default)(
                  '#asColorPicker-dropdown'
                );
                var self = void 0;
                if ($dropdown.length > 0) {
                  self = $dropdown.data(NAMESPACE$1);
                  if (self.opened) {
                    if (self.options.hideFireChange) {
                      self.apply();
                    } else {
                      self.cancel();
                    }
                  }

                  e.preventDefault();
                  e.stopPropagation();
                }
              }
            );
          }
        },
        {
          key: 'close',
          value: function close() {
            this.opened = false;
            this.$element.blur();
            this.$mask.hide();

            this.$dropdown.removeClass(this.classes.open);

            (0, _jquery2.default)(window).off(this.eventName('resize'));

            this._trigger('close');
          }
        },
        {
          key: 'clear',
          value: function clear() {
            this.val('');
          }
        },
        {
          key: 'cancel',
          value: function cancel() {
            this.close();

            this.set(this.originValue);
          }
        },
        {
          key: 'apply',
          value: function apply() {
            this._trigger('apply', this.color);
            this.close();
          }
        },
        {
          key: 'val',
          value: function val(value) {
            if (typeof value === 'undefined') {
              return this.color.toString();
            }

            this.set(value);
          }
        },
        {
          key: '_update',
          value: function _update() {
            this._trigger('update', this.color);
            this._updateInput();
          }
        },
        {
          key: '_updateInput',
          value: function _updateInput() {
            var value = this.color.toString();
            if (this.isEmpty) {
              value = '';
            }
            this._trigger('change', value);
            this.$element.val(value);
          }
        },
        {
          key: 'set',
          value: function set(value) {
            if (value !== '') {
              this.isEmpty = false;
            } else {
              this.isEmpty = true;
            }
            return this._set(value);
          }
        },
        {
          key: '_set',
          value: function _set(value) {
            if (typeof value === 'string') {
              this.color.val(value);
            } else {
              this.color.set(value);
            }

            this._update();
          }
        },
        {
          key: '_setup',
          value: function _setup() {
            this._trigger('setup', this.color);
          }
        },
        {
          key: 'get',
          value: function get() {
            return this.color;
          }
        },
        {
          key: 'enable',
          value: function enable() {
            this.disabled = false;
            this.$parent.addClass(this.classes.disabled);
            this._trigger('enable');
            return this;
          }
        },
        {
          key: 'disable',
          value: function disable() {
            this.disabled = true;
            this.$parent.removeClass(this.classes.disabled);
            this._trigger('disable');
            return this;
          }
        },
        {
          key: 'destroy',
          value: function destroy() {
            this.$element.unwrap();
            this.$element.off(this.eventName());
            this.$mask.remove();
            this.$dropdown.remove();

            this.initialized = false;
            this.$element.data(NAMESPACE$1, null);

            this._trigger('destroy');
            return this;
          }
        },
        {
          key: 'getString',
          value: function getString(name, def) {
            if (
              this.options.lang in LOCALIZATIONS &&
              typeof LOCALIZATIONS[this.options.lang][name] !== 'undefined'
            ) {
              return LOCALIZATIONS[this.options.lang][name];
            }
            return def;
          }
        }
      ],
      [
        {
          key: 'setLocalization',
          value: function setLocalization(lang, strings) {
            LOCALIZATIONS[lang] = strings;
          }
        },
        {
          key: 'registerComponent',
          value: function registerComponent(name, method) {
            COMPONENTS[name] = method;
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

    return AsColorPicker;
  })();

  AsColorPicker.registerComponent('alpha', alpha);
  AsColorPicker.registerComponent('hex', hex);
  AsColorPicker.registerComponent('hue', hue);
  AsColorPicker.registerComponent('saturation', saturation);
  AsColorPicker.registerComponent('buttons', buttons);
  AsColorPicker.registerComponent('trigger', trigger);
  AsColorPicker.registerComponent('clear', clear);
  AsColorPicker.registerComponent('info', info);
  AsColorPicker.registerComponent('palettes', palettes);
  AsColorPicker.registerComponent('preview', preview);
  AsColorPicker.registerComponent('gradient', gradient);

  // Chinese (cn) localization
  AsColorPicker.setLocalization('cn', {
    cancelText: '取消',
    applyText: '应用'
  });

  // German (de) localization
  AsColorPicker.setLocalization('de', {
    cancelText: 'Abbrechen',
    applyText: 'Wählen'
  });

  // Danish (dk) localization
  AsColorPicker.setLocalization('dk', {
    cancelText: 'annuller',
    applyText: 'Vælg'
  });

  // Spanish (es) localization
  AsColorPicker.setLocalization('es', {
    cancelText: 'Cancelar',
    applyText: 'Elegir'
  });

  // Finnish (fi) localization
  AsColorPicker.setLocalization('fi', {
    cancelText: 'Kumoa',
    applyText: 'Valitse'
  });

  // French (fr) localization
  AsColorPicker.setLocalization('fr', {
    cancelText: 'Annuler',
    applyText: 'Valider'
  });

  // Italian (it) localization
  AsColorPicker.setLocalization('it', {
    cancelText: 'annulla',
    applyText: 'scegli'
  });

  // Japanese (ja) localization
  AsColorPicker.setLocalization('ja', {
    cancelText: '中止',
    applyText: '選択'
  });

  // Russian (ru) localization
  AsColorPicker.setLocalization('ru', {
    cancelText: 'отмена',
    applyText: 'выбрать'
  });

  // Swedish (sv) localization
  AsColorPicker.setLocalization('sv', {
    cancelText: 'Avbryt',
    applyText: 'Välj'
  });

  // Turkish (tr) localization
  AsColorPicker.setLocalization('tr', {
    cancelText: 'Avbryt',
    applyText: 'Välj'
  });

  var info$1 = {
    version: '0.4.4'
  };

  var NAMESPACE = 'asColorPicker';
  var OtherAsColorPicker = _jquery2.default.fn.asColorPicker;

  var jQueryAsColorPicker = function jQueryAsColorPicker(options) {
    for (
      var _len2 = arguments.length,
        args = Array(_len2 > 1 ? _len2 - 1 : 0),
        _key2 = 1;
      _key2 < _len2;
      _key2++
    ) {
      args[_key2 - 1] = arguments[_key2];
    }

    if (typeof options === 'string') {
      var method = options;

      if (/^_/.test(method)) {
        return false;
      } else if (
        /^(get)$/.test(method) ||
        (method === 'val' && args.length === 0)
      ) {
        var instance = this.first().data(NAMESPACE);
        if (instance && typeof instance[method] === 'function') {
          return instance[method].apply(instance, args);
        }
      } else {
        return this.each(function() {
          var instance = _jquery2.default.data(this, NAMESPACE);
          if (instance && typeof instance[method] === 'function') {
            instance[method].apply(instance, args);
          }
        });
      }
    }

    return this.each(function() {
      if (!(0, _jquery2.default)(this).data(NAMESPACE)) {
        (0, _jquery2.default)(this).data(
          NAMESPACE,
          new AsColorPicker(this, options)
        );
      }
    });
  };

  _jquery2.default.fn.asColorPicker = jQueryAsColorPicker;

  _jquery2.default.asColorPicker = _jquery2.default.extend(
    {
      setDefaults: AsColorPicker.setDefaults,
      registerComponent: AsColorPicker.registerComponent,
      setLocalization: AsColorPicker.setLocalization,
      noConflict: function noConflict() {
        _jquery2.default.fn.asColorPicker = OtherAsColorPicker;
        return jQueryAsColorPicker;
      }
    },
    info$1
  );
});
