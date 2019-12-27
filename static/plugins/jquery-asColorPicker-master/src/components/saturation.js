import AsColor from 'jquery-asColor';

// saturation
export default {
  defaults: {
    template(namespace) {
      return `<div class="${namespace}-saturation"><i><b></b></i></div>`;
    }
  },

  width: 0,
  height: 0,
  size: 6,
  data: {},

  init: function(api, options) {
    const that = this;
    this.options = $.extend(this.defaults, options);
    this.api = api;

    //build element and add component to picker
    this.$saturation = $(this.options.template.call(that, api.namespace)).appendTo(api.$dropdown);
    this.$handle = this.$saturation.find('i');

    api.$element.on('asColorPicker::firstOpen', () => {
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

    api.$element.on('asColorPicker::update asColorPicker::setup', (e, api, color) => {
      that.update(color);
    });
  },

  bindEvents: function() {
    const that = this;

    this.$saturation.on(this.api.eventName('mousedown'), e => {
      const rightclick = (e.which) ? (e.which === 3) : (e.button === 2);
      if (rightclick) {
        return false;
      }
      that.mousedown(e);
    });
  },

  mousedown: function(e) {
    const offset = this.$saturation.offset();

    this.data.startY = e.pageY;
    this.data.startX = e.pageX;
    this.data.top = e.pageY - offset.top;
    this.data.left = e.pageX - offset.left;
    this.data.cach = {};

    this.move(this.data.left, this.data.top);

    this.mousemove = function(e) {
      const x = this.data.left + (e.pageX || this.data.startX) - this.data.startX;
      const y = this.data.top + (e.pageY || this.data.startY) - this.data.startY;
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

  move: function(x, y, update) {
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
        v: 1 - (y / this.height)
      });
    }
  },

  update: function(color) {
    if (color.value.h === undefined) {
      color.value.h = 0;
    }
    this.$saturation.css('backgroundColor', AsColor.HSLtoHEX({
      h: color.value.h,
      s: 1,
      l: 0.5
    }));

    const x = color.value.s * this.width;
    const y = (1 - color.value.v) * this.height;

    this.move(x, y, false);
  },

  moveLeft: function() {
    const step = this.step.left;
    const data = this.data;
    data.left = Math.max(0, Math.min(this.width, data.left - step));
    this.move(data.left, data.top);
  },

  moveRight: function() {
    const step = this.step.left;
    const data = this.data;
    data.left = Math.max(0, Math.min(this.width, data.left + step));
    this.move(data.left, data.top);
  },

  moveUp: function() {
    const step = this.step.top;
    const data = this.data;
    data.top = Math.max(0, Math.min(this.width, data.top - step));
    this.move(data.left, data.top);
  },

  moveDown: function() {
    const step = this.step.top;
    const data = this.data;
    data.top = Math.max(0, Math.min(this.width, data.top + step));
    this.move(data.left, data.top);
  },

  keyboard: function() {
    let keyboard;
    const that = this;
    if (this.api._keyboard) {
      keyboard = $.extend(true, {}, this.api._keyboard);
    } else {
      return false;
    }

    this.$saturation.attr('tabindex', '0').on('focus', () => {
      keyboard.attach({
        left() {
          that.moveLeft();
        },
        right() {
          that.moveRight();
        },
        up() {
          that.moveUp();
        },
        down() {
          that.moveDown();
        }
      });
      return false;
    }).on('blur', () => {
      keyboard.detach();
    });
  },

  destroy: function() {
    $(document).off({
      mousemove: this.mousemove,
      mouseup: this.mouseup
    });
  }
};
