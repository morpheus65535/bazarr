// trigger
export default {
  defaults: {
    template(namespace) {
      return `<div class="${namespace}-trigger"><span></span></div>`;
    }
  },

  init: function(api, options) {
    this.options = $.extend(this.defaults, options);
    api.$trigger = $(this.options.template.call(this, api.namespace));
    this.$triggerInner = api.$trigger.children('span');

    api.$trigger.insertAfter(api.$element);
    api.$trigger.on('click', () => {
      if (!api.opened) {
        api.open();
      } else {
        api.close();
      }
      return false;
    });
    const that = this;
    api.$element.on('asColorPicker::update', (e, api, color, gradient) => {
      if (typeof gradient === 'undefined') {
        gradient = false;
      }
      that.update(color, gradient);
    });

    this.update(api.color);
  },

  update: function(color, gradient) {
    if (gradient) {
      this.$triggerInner.css('background', gradient.toString(true));
    } else {
      this.$triggerInner.css('background', color.toRGBA());
    }
  },

  destroy: function(api) {
    api.$trigger.remove();
  }
};
