// buttons
export default {
  defaults: {
    apply: false,
    cancel: true,
    applyText: null,
    cancelText: null,
    template(namespace) {
      return `<div class="${namespace}-buttons"></div>`;
    },
    applyTemplate(namespace) {
      return `<a href="#" alt="${this.options.applyText}" class="${namespace}-buttons-apply">${this.options.applyText}</a>`;
    },
    cancelTemplate(namespace) {
      return `<a href="#" alt="${this.options.cancelText}" class="${namespace}-buttons-apply">${this.options.cancelText}</a>`;
    }
  },

  init: function(api, options) {
    const that = this;

    this.options = $.extend(this.defaults, {
      applyText: api.getString('applyText', 'apply'),
      cancelText: api.getString('cancelText', 'cancel')
    }, options);
    this.$buttons = $(this.options.template.call(this, api.namespace)).appendTo(api.$dropdown);

    api.$element.on('asColorPicker::firstOpen', () => {
      if (that.options.apply) {
        that.$apply = $(that.options.applyTemplate.call(that, api.namespace)).appendTo(that.$buttons).on('click', () => {
          api.apply();
          return false;
        });
      }

      if (that.options.cancel) {
        that.$cancel = $(that.options.cancelTemplate.call(that, api.namespace)).appendTo(that.$buttons).on('click', () => {
          api.cancel();
          return false;
        });
      }
    });
  }
};
