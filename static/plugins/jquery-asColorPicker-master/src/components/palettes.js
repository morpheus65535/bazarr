import AsColor from 'jquery-asColor';

// palettes
function noop() {
  return;
}
if (!window.localStorage) {
  window.localStorage = noop;
}

export default {
  defaults: {
    template(namespace) {
      return `<ul class="${namespace}-palettes"></ul>`;
    },
    item(namespace, color) {
      return `<li data-color="${color}"><span style="background-color:${color}" /></li>`;
    },
    colors: ['white', 'black', 'red', 'blue', 'yellow'],
    max: 10,
    localStorage: true
  },

  init: function(api, options) {
    const that = this;
    let colors;
    const asColor = AsColor();

    this.options = $.extend(true, {}, this.defaults, options);
    this.colors = [];
    let localKey;

    if (this.options.localStorage) {
      localKey = `${api.namespace}_palettes_${api.id}`;
      colors = this.getLocal(localKey);
      if (!colors) {
        colors = this.options.colors;
        this.setLocal(localKey, colors);
      }
    } else {
      colors = this.options.colors;
    }

    for (const i in colors) {
      if(Object.hasOwnProperty.call(colors, i)){
        this.colors.push(asColor.val(colors[i]).toRGBA());
      }
    }

    let list = '';
    $.each(this.colors, (i, color) => {
      list += that.options.item(api.namespace, color);
    });

    this.$palettes = $(this.options.template.call(this, api.namespace)).html(list).appendTo(api.$dropdown);

    this.$palettes.on(api.eventName('click'), 'li', function(e) {
      const color = $(this).data('color');
      api.set(color);

      e.preventDefault();
      e.stopPropagation();
    });

    api.$element.on('asColorPicker::apply', (e, api, color) => {
      if (typeof color.toRGBA !== 'function') {
        color = color.get().color;
      }

      const rgba = color.toRGBA();
      if ($.inArray(rgba, that.colors) === -1) {
        if (that.colors.length >= that.options.max) {
          that.colors.shift();
          that.$palettes.find('li').eq(0).remove();
        }

        that.colors.push(rgba);

        that.$palettes.append(that.options.item(api.namespace, color));

        if (that.options.localStorage) {
          that.setLocal(localKey, that.colors);
        }
      }
    });
  },

  setLocal: function(key, value) {
    const jsonValue = JSON.stringify(value);

    localStorage[key] = jsonValue;
  },

  getLocal: function(key) {
    const value = localStorage[key];

    return value ? JSON.parse(value) : value;
  }
};
