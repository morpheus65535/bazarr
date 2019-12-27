// hex
export default {
  init: function(api) {
    const template = `<input type="text" class="${api.namespace}-hex" />`;
    this.$hex = $(template).appendTo(api.$dropdown);

    this.$hex.on('change', function() {
      api.set(this.value);
    });

    const that = this;
    api.$element.on('asColorPicker::update asColorPicker::setup', (e, api, color) => {
      that.update(color);
    });
  },

  update: function(color) {
    this.$hex.val(color.toHEX());
  }
};
