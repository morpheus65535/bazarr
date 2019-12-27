// clear
export default {
  defaults: {
    template(namespace) {
      return `<a href="#" class="${namespace}-clear"></a>`;
    }
  },

  init: function(api, options) {
    if (api.options.hideInput) {
      return;
    }
    this.options = $.extend(this.defaults, options);
    this.$clear = $(this.options.template.call(this, api.namespace)).insertAfter(api.$element);

    this.$clear.on('click', () => {
      api.clear();
      return false;
    });
  }
};
