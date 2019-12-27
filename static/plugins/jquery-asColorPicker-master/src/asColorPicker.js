import $ from 'jquery';
import DEFAULTS from './defaults';
import MODES from './modes';

import AsColor from 'jquery-asColor';

import alpha from './components/alpha';
import hex from './components/hex';
import hue from './components/hue';
import saturation from './components/saturation';
import buttons from './components/buttons';
import trigger from './components/trigger';
import clear from './components/clear';
import info from './components/info';
import palettes from './components/palettes';
import preview from './components/preview';
import gradient from './components/gradient';

const NAMESPACE = 'asColorPicker';
const COMPONENTS = {};
const LOCALIZATIONS = {
  en: {
    cancelText: 'cancel',
    applyText: 'apply'
  }
};

let id = 0;

function createId(api) {
  api.id = id;
  id++;
}

class AsColorPicker {
  constructor(element, options) {
    this.element = element;
    this.$element = $(element);

    //flag
    this.opened = false;
    this.firstOpen = true;
    this.disabled = false;
    this.initialed = false;
    this.originValue = this.element.value;
    this.isEmpty = false;

    createId(this);

    this.options = $.extend(true, {}, DEFAULTS, options, this.$element.data());
    this.namespace = this.options.namespace;

    this.classes = {
      wrap: `${this.namespace}-wrap`,
      dropdown: `${this.namespace}-dropdown`,
      input: `${this.namespace}-input`,
      skin: `${this.namespace}_${this.options.skin}`,
      open: `${this.namespace}_open`,
      mask: `${this.namespace}-mask`,
      hideInput: `${this.namespace}_hideInput`,
      disabled: `${this.namespace}_disabled`,
      mode: `${this.namespace}-mode_${this.options.mode}`
    };

    if (this.options.hideInput) {
      this.$element.addClass(this.classes.hideInput);
    }

    this.components = MODES[this.options.mode];
    this._components = $.extend(true, {}, COMPONENTS);

    this._trigger('init');
    this.init();
  }

  _trigger(eventType, ...params) {
    let data = [this].concat(params);

    // event
    this.$element.trigger(`${NAMESPACE}::${eventType}`, data);

    // callback
    eventType = eventType.replace(/\b\w+\b/g, (word) => {
      return word.substring(0, 1).toUpperCase() + word.substring(1);
    });
    let onFunction = `on${eventType}`;

    if (typeof this.options[onFunction] === 'function') {
      this.options[onFunction].apply(this, params);
    }
  }

  eventName(events) {
    if (typeof events !== 'string' || events === '') {
      return `.${this.options.namespace}`;
    }
    events = events.split(' ');

    let length = events.length;
    for (let i = 0; i < length; i++) {
      events[i] = `${events[i]}.${this.options.namespace}`;
    }
    return events.join(' ');
  }

  init() {
    this.color = AsColor(this.element.value, this.options.color);

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

  _create() {
    this.$dropdown = $(`<div class="${this.classes.dropdown}" data-mode="${this.options.mode}"></div>`);
    this.$element.wrap(`<div class="${this.classes.wrap}"></div>`).addClass(this.classes.input);

    this.$wrap = this.$element.parent();
    this.$body = $('body');

    this.$dropdown.data(NAMESPACE, this);

    let component;
    $.each(this.components, (key, options) => {
      if (options === true) {
        options = {};
      }
      if (this.options[key] !== undefined) {
        options = $.extend(true, {}, options, this.options[key]);
      }
      if (Object.hasOwnProperty.call(this._components, key)) {
        component = this._components[key];
        component.init(this, options);
      }
    });

    this._trigger('create');
  }

  _bindEvent() {
    this.$element.on(this.eventName('click'), () => {
      if (!this.opened) {
        this.open();
      }
      return false;
    });

    this.$element.on(this.eventName('keydown'), (e) => {
      if (e.keyCode === 9) {
        this.close();
      } else if (e.keyCode === 13) {
        this.val(this.element.value);
        this.close();
      }
    });

    this.$element.on(this.eventName('keyup'), () => {
      if (this.color.matchString(this.element.value)) {
        this.val(this.element.value);
      }
    });
  }

  opacity(v) {
    if (v) {
      this.color.alpha(v);
    } else {
      return this.color.alpha();
    }
  }

  position() {
    const hidden = !this.$element.is(':visible');
    const offset = hidden ? this.$trigger.offset() : this.$element.offset();
    const height = hidden ? this.$trigger.outerHeight() : this.$element.outerHeight();
    const width = hidden ? this.$trigger.outerWidth() : this.$element.outerWidth() + this.$trigger.outerWidth();
    const pickerWidth = this.$dropdown.outerWidth(true);
    const pickerHeight = this.$dropdown.outerHeight(true);
    let top;
    let left;

    if (pickerHeight + offset.top > $(window).height() + $(window).scrollTop()) {
      top = offset.top - pickerHeight;
    } else {
      top = offset.top + height;
    }

    if (pickerWidth + offset.left > $(window).width() + $(window).scrollLeft()) {
      left = offset.left - pickerWidth + width;
    } else {
      left = offset.left;
    }

    this.$dropdown.css({
      position: 'absolute',
      top,
      left
    });
  }

  open() {
    if (this.disabled) {
      return;
    }
    this.originValue = this.element.value;

    if (this.$dropdown[0] !== this.$body.children().last()[0]) {
      this.$dropdown.detach().appendTo(this.$body);
    }

    this.$mask = $(`.${this.classes.mask}`);
    if (this.$mask.length === 0) {
      this.createMask();
    }

    // ensure the mask is always right before the dropdown
    if (this.$dropdown.prev()[0] !== this.$mask[0]) {
      this.$dropdown.before(this.$mask);
    }

    $("#asColorPicker-dropdown").removeAttr("id");
    this.$dropdown.attr("id", "asColorPicker-dropdown");

    // show the mask
    this.$mask.show();

    this.position();

    $(window).on(this.eventName('resize'), $.proxy(this.position, this));

    this.$dropdown.addClass(this.classes.open);

    this.opened = true;

    if (this.firstOpen) {
      this.firstOpen = false;
      this._trigger('firstOpen');
    }
    this._setup();
    this._trigger('open');
  }

  createMask() {
    this.$mask = $(document.createElement("div"));
    this.$mask.attr("class", this.classes.mask);
    this.$mask.hide();
    this.$mask.appendTo(this.$body);

    this.$mask.on(this.eventName("mousedown touchstart click"), e => {
      const $dropdown = $("#asColorPicker-dropdown");
      let self;
      if ($dropdown.length > 0) {
        self = $dropdown.data(NAMESPACE);
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
    });
  }

  close() {
    this.opened = false;
    this.$element.blur();
    this.$mask.hide();

    this.$dropdown.removeClass(this.classes.open);

    $(window).off(this.eventName('resize'));

    this._trigger('close');
  }

  clear() {
    this.val('');
  }

  cancel() {
    this.close();

    this.set(this.originValue);
  }

  apply() {
    this._trigger('apply', this.color);
    this.close();
  }

  val(value) {
    if (typeof value === 'undefined') {
      return this.color.toString();
    }

    this.set(value);
  }

  _update() {
    this._trigger('update', this.color);
    this._updateInput();
  }

  _updateInput() {
    let value = this.color.toString();
    if (this.isEmpty) {
      value = '';
    }
    this._trigger('change', value);
    this.$element.val(value);
  }

  set(value) {
    if (value !== '') {
      this.isEmpty = false;
    } else {
      this.isEmpty = true;
    }
    return this._set(value);
  }

  _set(value) {
    if (typeof value === 'string') {
      this.color.val(value);
    } else {
      this.color.set(value);
    }

    this._update();
  }

  _setup() {
    this._trigger('setup', this.color);
  }

  get() {
    return this.color;
  }

  enable() {
    this.disabled = false;
    this.$parent.addClass(this.classes.disabled);
    this._trigger('enable');
    return this;
  }

  disable() {
    this.disabled = true;
    this.$parent.removeClass(this.classes.disabled);
    this._trigger('disable');
    return this;
  }

  destroy() {
    this.$element.unwrap();
    this.$element.off(this.eventName());
    this.$mask.remove();
    this.$dropdown.remove();

    this.initialized = false;
    this.$element.data(NAMESPACE, null);

    this._trigger('destroy');
    return this;
  }

  getString(name, def) {
    if(this.options.lang in LOCALIZATIONS && typeof LOCALIZATIONS[this.options.lang][name] !== 'undefined') {
      return LOCALIZATIONS[this.options.lang][name];
    }
    return def;
  }

  static setLocalization(lang, strings) {
    LOCALIZATIONS[lang] = strings;
  }

  static registerComponent(name, method) {
    COMPONENTS[name] = method;
  }

  static setDefaults(options) {
    $.extend(true, DEFAULTS, $.isPlainObject(options) && options);
  }
}

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

export default AsColorPicker;
