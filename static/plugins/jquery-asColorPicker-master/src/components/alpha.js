// alpha
export default {
  size: 150,

  defaults: {
    direction: 'vertical', // horizontal
    template(namespace) {
      return `<div class="${namespace}-alpha ${namespace}-alpha-${this.direction}"><i></i></div>`;
    }
  },

  data: {},

  init: function(api, options) {
    const that = this;

    this.options = $.extend(this.defaults, options);
    that.direction = this.options.direction;
    this.api = api;

    this.$alpha = $(this.options.template.call(that, api.namespace)).appendTo(api.$dropdown);
    this.$handle = this.$alpha.find('i');

    api.$element.on('asColorPicker::firstOpen', () => {
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

    api.$element.on('asColorPicker::update asColorPicker::setup', (e, api, color) => {
      that.update(color);
    });
  },

  bindEvents: function() {
    const that = this;
    this.$alpha.on(this.api.eventName('mousedown'), e => {
      const rightclick = (e.which) ? (e.which === 3) : (e.button === 2);
      if (rightclick) {
        return false;
      }
      $.proxy(that.mousedown, that)(e);
    });
  },

  mousedown: function(e) {
    const offset = this.$alpha.offset();
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
      let position;
      if (this.direction === 'vertical') {
        position = this.data.top + (e.pageY || this.data.startY) - this.data.startY;
      } else {
        position = this.data.left + (e.pageX || this.data.startX) - this.data.startX;
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

  move: function(position, alpha, update) {
    position = Math.max(0, Math.min(this.size, position));
    this.data.cach = position;
    if (typeof alpha === 'undefined') {
      alpha = 1 - (position / this.size);
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

  moveLeft: function() {
    const step = this.step;
    const data = this.data;
    data.left = Math.max(0, Math.min(this.width, data.left - step));
    this.move(data.left);
  },

  moveRight: function() {
    const step = this.step;
    const data = this.data;
    data.left = Math.max(0, Math.min(this.width, data.left + step));
    this.move(data.left);
  },

  moveUp: function() {
    const step = this.step;
    const data = this.data;
    data.top = Math.max(0, Math.min(this.width, data.top - step));
    this.move(data.top);
  },

  moveDown: function() {
    const step = this.step;
    const data = this.data;
    data.top = Math.max(0, Math.min(this.width, data.top + step));
    this.move(data.top);
  },

  keyboard: function() {
    let keyboard;
    const that = this;
    if (this.api._keyboard) {
      keyboard = $.extend(true, {}, this.api._keyboard);
    } else {
      return false;
    }

    this.$alpha.attr('tabindex', '0').on('focus', function() {
      if (this.direction === 'vertical') {
        keyboard.attach({
          up() {
            that.moveUp();
          },
          down() {
            that.moveDown();
          }
        });
      } else {
        keyboard.attach({
          left() {
            that.moveLeft();
          },
          right() {
            that.moveRight();
          }
        });
      }
      return false;
    }).on('blur', () => {
      keyboard.detach();
    });
  },

  update: function(color) {
    const position = this.size * (1 - color.value.a);
    this.$alpha.css('backgroundColor', color.toHEX());

    this.move(position, color.value.a, false);
  },

  destroy: function() {
    $(document).off({
      mousemove: this.mousemove,
      mouseup: this.mouseup
    });
  }
};
