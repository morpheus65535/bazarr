import AsGradient from 'jquery-asGradient';
import AsColor from 'jquery-asColor';

// gradient
function conventToPercentage(n) {
  if (n < 0) {
    n = 0;
  } else if (n > 1) {
    n = 1;
  }
  return `${n * 100}%`;
}

var Gradient = function(api, options) {
  this.api = api;
  this.options = options;
  this.classes = {
    enable: `${api.namespace}-gradient_enable`,
    marker: `${api.namespace}-gradient-marker`,
    active: `${api.namespace}-gradient-marker_active`,
    focus: `${api.namespace}-gradient_focus`
  };
  this.isEnabled = false;
  this.initialized = false;
  this.current = null;
  this.value = AsGradient(this.options.settings);
  this.$doc = $(document);

  const that = this;
  $.extend(that, {
    init() {
      that.$wrap = $(that.options.template.call(that)).appendTo(api.$dropdown);

      that.$gradient = that.$wrap.filter(`.${api.namespace}-gradient`);

      this.angle.init();
      this.preview.init();
      this.markers.init();
      this.wheel.init();

      this.bind();

      if (that.options.switchable === false || this.value.matchString(api.element.value)) {
        that.enable();
      }
      this.initialized = true;
    },
    bind() {
      const namespace = api.namespace;

      that.$gradient.on('update', () => {
        const current = that.value.getById(that.current);

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
        that.$wrap.on('click', `.${namespace}-gradient-switch`, () => {
          if (that.isEnabled) {
            that.disable();
          } else {
            that.enable();
          }

          return false;
        });
      }

      that.$wrap.on('click', `.${namespace}-gradient-cancel`, () => {
        if (that.options.switchable === false || AsGradient.matchString(api.originValue)) {
          that.overrideCore();
        }

        api.cancel();

        return false;
      });
    },
    overrideCore() {
      api.set = value => {
        if (value !== '') {
          api.isEmpty = false;
        } else {
          api.isEmpty = true;
        }
        if (typeof value === 'string') {
          if (that.options.switchable === false || AsGradient.matchString(value)) {
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
          const current = that.value.getById(that.current);

          if (current) {
            current.color.val(value)
            api._trigger('update', current.color, that.value);
          }

          that.$gradient.trigger('update', {
            id: that.current,
            stop: current
          });
        }
      };

      api._setup = () => {
        const current = that.value.getById(that.current);

        api._trigger('setup', current.color);
      };
    },
    revertCore() {
      api.set = $.proxy(api._set, api);
      api._setup = () => {
        api._trigger('setup', api.color);
      };
    },
    preview: {
      init() {
        that.$preview = that.$gradient.find(`.${api.namespace}-gradient-preview`);

        that.$gradient.on('add del update empty', () => {
          this.render();
        });
      },
      render() {
        that.$preview.css({
          'background-image': that.value.toStringWithAngle('to right', true),
        });
        that.$preview.css({
          'background-image': that.value.toStringWithAngle('to right'),
        });
      }
    },
    markers: {
      width: 160,
      init() {
        that.$markers = that.$gradient.find(`.${api.namespace}-gradient-markers`).attr('tabindex', 0);

        that.$gradient.on('add', (e, data) => {
          this.add(data.stop);
        });

        that.$gradient.on('active', (e, data) => {
          this.active(data.id);
        });

        that.$gradient.on('del', (e, data) => {
          this.del(data.id);
        });

        that.$gradient.on('update', (e, data) => {
          if (data.stop) {
            this.update(data.stop.id, data.stop.color);
          }
        });

        that.$gradient.on('empty', () => {
          this.empty();
        });

        that.$markers.on(that.api.eventName('mousedown'), e => {
          const rightclick = (e.which) ? (e.which === 3) : (e.button === 2);
          if (rightclick) {
            return false;
          }

          const position = parseFloat((e.pageX - that.$markers.offset().left) / that.markers.width, 10);
          that.add('#fff', position);
          return false;
        });

        /* eslint consistent-this: "off" */
        let self = this;
        that.$markers.on(that.api.eventName('mousedown'), 'li', function(e) {
          const rightclick = (e.which) ? (e.which === 3) : (e.button === 2);
          if (rightclick) {
            return false;
          }
          self.mousedown(this, e);
          return false;
        });

        that.$doc.on(that.api.eventName('keydown'), e => {
          if (that.api.opened && that.$markers.is(`.${that.classes.focus}`)) {

            const key = e.keyCode || e.which;
            if (key === 46 || key === 8) {
              if (that.value.length <= 2) {
                return false;
              }

              that.del(that.current);

              return false;
            }
          }
        });

        that.$markers.on(that.api.eventName('focus'), () => {
          that.$markers.addClass(that.classes.focus);
        }).on(that.api.eventName('blur'), () => {
          that.$markers.removeClass(that.classes.focus);
        });

        that.$markers.on(that.api.eventName('click'), 'li', function() {
          const id = $(this).data('id');
          that.active(id);
        });
      },
      getMarker(id) {
        return that.$markers.find(`[data-id="${id}"]`);
      },
      update(id, color) {
        const $marker = this.getMarker(id);
        $marker.find('span').css('background-color', color.toHEX());
        $marker.find('i').css('background-color', color.toHEX());
      },
      add(stop) {
        $(`<li data-id="${stop.id}" style="left:${conventToPercentage(stop.position)}" class="${that.classes.marker}"><span style="background-color: ${stop.color.toHEX()}"></span><i style="background-color: ${stop.color.toHEX()}"></i></li>`).appendTo(that.$markers);
      },
      empty() {
        that.$markers.html('');
      },
      del(id) {
        const $marker = this.getMarker(id);
        let $to = $marker.prev();
        if ($to.length === 0) {
          $to = $marker.next();
        }

        that.active($to.data('id'));
        $marker.remove();
      },
      active(id) {
        that.$markers.children().removeClass(that.classes.active);

        const $marker = this.getMarker(id);
        $marker.addClass(that.classes.active);

        that.$markers.focus();
        // that.api._trigger('apply', that.value.getById(id).color);
      },
      mousedown(marker, e) {
        const self = this;
        /* eslint consistent-this: "off" */
        const id = $(marker).data('id');
        const first = $(marker).position().left;
        const start = e.pageX;
        let end;

        this.mousemove = function(e) {
          end = e.pageX || start;
          const position = (first + end - start) / this.width;
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
      move(marker, position, id) {
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
          position
        });
      },
    },
    wheel: {
      init() {
        that.$wheel = that.$gradient.find(`.${api.namespace}-gradient-wheel`);
        that.$pointer = that.$wheel.find('i');

        that.$gradient.on('update', (e, data) => {
          if (typeof data.angle !== 'undefined') {
            this.position(data.angle);
          }
        });

        that.$wheel.on(that.api.eventName('mousedown'), e => {
          const rightclick = (e.which) ? (e.which === 3) : (e.button === 2);
          if (rightclick) {
            return false;
          }
          this.mousedown(e, that);
          return false;
        });
      },
      mousedown(e, that) {
        const offset = that.$wheel.offset();
        const r = that.$wheel.width() / 2;
        const startX = offset.left + r;
        const startY = offset.top + r;
        const $doc = that.$doc;

        this.r = r;

        this.wheelMove = e => {
          const x = e.pageX - startX;
          const y = startY - e.pageY;

          const position = this.getPosition(x, y);
          const angle = this.calAngle(position.x, position.y);
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
      getPosition(a, b) {
        const r = this.r;
        const x = a / Math.sqrt(a * a + b * b) * r;
        const y = b / Math.sqrt(a * a + b * b) * r;
        return {
          x,
          y
        };
      },
      calAngle(x, y) {
        const deg = Math.round(Math.atan(Math.abs(x / y)) * (180 / Math.PI));
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
      set(value) {
        that.value.angle(value);
        that.$gradient.trigger('update', {
          angle: value
        });
      },
      position(angle) {
        const r = this.r || that.$wheel.width() / 2;
        const pos = this.calPointer(angle, r);
        that.$pointer.css({
          left: pos.x,
          top: pos.y
        });
      },
      calPointer(angle, r) {
        const x = Math.sin(angle * Math.PI / 180) * r;
        const y = Math.cos(angle * Math.PI / 180) * r;
        return {
          x: r + x,
          y: r - y
        };
      }
    },
    angle: {
      init() {
        that.$angle = that.$gradient.find(`.${api.namespace}-gradient-angle`);

        that.$angle.on(that.api.eventName('blur'), function() {
          that.setAngle(this.value);
          return false;
        }).on(that.api.eventName('keydown'), function(e) {
          const key = e.keyCode || e.which;
          if (key === 13) {
            that.api.isEmpty = false;
            $(this).blur();
            return false;
          }
        });

        that.$gradient.on('update', (e, data) => {
          if (typeof data.angle !== 'undefined') {
            that.$angle.val(data.angle);
          }
        });
      },
      set(value) {
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

  enable(value) {
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

    if (!AsGradient.matchString(value) && this._last) {
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
  val(string) {
    if (string !== '' && this.value.toString() === string) {
      return;
    }
    this.empty();
    this.value.val(string);
    this.value.reorder();

    if (this.value.length < 2) {
      let fill = string;

      if (!AsColor.matchString(string)) {
        fill = 'rgba(0,0,0,1)';
      }

      if (this.value.length === 0) {
        this.value.append(fill, 0);
      }
      if (this.value.length === 1) {
        this.value.append(fill, 1);
      }
    }

    let stop;
    for (let i = 0; i < this.value.length; i++) {
      stop = this.value.get(i);
      if (stop) {
        this.$gradient.trigger('add', {
          stop
        });
      }
    }

    this.active(stop.id);
  },
  disable() {
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
  active(id) {
    if (this.current !== id) {
      this.current = id;
      this.value.setCurrentById(id);

      this.$gradient.trigger('active', {
        id
      });
    }
  },
  empty() {
    this.value.empty();
    this.$gradient.trigger('empty');
  },
  add(color, position) {
    const stop = this.value.insert(color, position);
    this.api.isEmpty = false;
    this.value.reorder();

    this.$gradient.trigger('add', {
      stop
    });

    this.active(stop.id);

    this.$gradient.trigger('update', {
      stop
    });
    return stop;
  },
  del(id) {
    if (this.value.length <= 2) {
      return;
    }
    this.value.removeById(id);
    this.value.reorder();
    this.$gradient.trigger('del', {
      id
    });

    this.$gradient.trigger('update', {});
  },
  setAngle(value) {
    this.value.angle(value);
    this.$gradient.trigger('update', {
      angle: value
    });
  }
};


export default {
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
    template() {
      const namespace = this.api.namespace;
      let control = `<div class="${namespace}-gradient-control">`;
      if (this.options.switchable) {
        control += `<a href="#" class="${namespace}-gradient-switch">${this.options.switchText}</a>`;
      }
      control += `<a href="#" class="${namespace}-gradient-cancel">${this.options.cancelText}</a></div>`;

      return `${control}<div class="${namespace}-gradient"><div class="${namespace}-gradient-preview"><ul class="${namespace}-gradient-markers"></ul></div><div class="${namespace}-gradient-wheel"><i></i></div><input class="${namespace}-gradient-angle" type="text" value="" size="3" /></div>`;
    }
  },

  init: function(api, options) {
    const that = this;

    api.$element.on('asColorPicker::ready', (event, instance) => {
      if (instance.options.mode !== 'gradient') {
        return;
      }

      that.defaults.settings.color = api.options.color;
      options = $.extend(true, that.defaults, options);

      api.gradient = new Gradient(api, options);
    });
  }
};
