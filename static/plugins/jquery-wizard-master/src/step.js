import $ from 'jquery';
import Support from './support';
import * as util from './util';

class Step {
  constructor(element, wizard, index) {
    this.TRANSITION_DURATION = 200;

    this.initialize(element, wizard, index);
  }

  initialize(element, wizard, index) {

    this.$element = $(element);
    this.wizard = wizard;

    this.events = {};
    this.loader = null;
    this.loaded = false;

    this.validator = this.wizard.options.validator;

    this.states = {
      done: false,
      error: false,
      active: false,
      disabled: false,
      activing: false
    };

    this.index = index;
    this.$element.data('wizard-index', index);


    this.$pane = this.getPaneFromTarget();

    if (!this.$pane) {
      this.$pane = this.wizard.options.getPane.call(this.wizard, index, element);
    }

    this.setValidatorFromData();
    this.setLoaderFromData();
  }

  getPaneFromTarget() {
    let selector = this.$element.data('target');

    if (!selector) {
      selector = this.$element.attr('href');
      selector = selector && selector.replace(/.*(?=#[^\s]*$)/, '');
    }

    if (selector) {
      return $(selector);
    }
    return null;
  }

  setup() {
    const current = this.wizard.currentIndex();
    if (this.index === current) {
      this.enter('active');

      if (this.loader) {
        this.load();
      }
    } else if (this.index > current) {
      this.enter('disabled');
    }

    this.$element.attr('aria-expanded', this.is('active'));
    this.$pane.attr('aria-expanded', this.is('active'));

    const classes = this.wizard.options.classes;
    if (this.is('active')) {
      this.$pane.addClass(classes.pane.active);
    } else {
      this.$pane.removeClass(classes.pane.active);
    }
  }

  show(callback) {
    if (this.is('activing') || this.is('active')) {
      return;
    }

    this.trigger('beforeShow');
    this.enter('activing');

    const classes = this.wizard.options.classes;

    this.$element
      .attr('aria-expanded', true);

    this.$pane
      .addClass(classes.pane.activing)
      .addClass(classes.pane.active)
      .attr('aria-expanded', true);

    const complete = function () {
      this.$pane.removeClass(classes.pane.activing);

      this.leave('activing');
      this.enter('active');
      this.trigger('afterShow');

      if ($.isFunction(callback)) {
        callback.call(this);
      }
    };

    if (!Support.transition) {
      complete.call(this);
      return;
    }

    this.$pane.one(Support.transition.end, $.proxy(complete, this));

    util.emulateTransitionEnd(this.$pane, this.TRANSITION_DURATION);
  }

  hide(callback) {
    if (this.is('activing') || !this.is('active')) {
      return;
    }

    this.trigger('beforeHide');
    this.enter('activing');

    const classes = this.wizard.options.classes;

    this.$element
      .attr('aria-expanded', false);

    this.$pane
      .addClass(classes.pane.activing)
      .removeClass(classes.pane.active)
      .attr('aria-expanded', false);

    const complete = function () {
      this.$pane
        .removeClass(classes.pane.activing);

      this.leave('activing');
      this.leave('active');
      this.trigger('afterHide');

      if ($.isFunction(callback)) {
        callback.call(this);
      }
    };

    if (!Support.transition) {
      complete.call(this);
      return;
    }

    this.$pane.one(Support.transition.end, $.proxy(complete, this));

    util.emulateTransitionEnd(this.$pane, this.TRANSITION_DURATION);
  }

  empty() {
    this.$pane.empty();
  }

  load(callback) {
    const that = this;
    let loader = this.loader;

    if ($.isFunction(loader)) {
      loader = loader.call(this.wizard, this);
    }

    if (this.wizard.options.cacheContent && this.loaded) {
      if ($.isFunction(callback)) {
        callback.call(this);
      }
      return;
    }

    this.trigger('beforeLoad');
    this.enter('loading');

    function setContent(content) {
      that.$pane.html(content);

      that.leave('loading');
      that.loaded = true;
      that.trigger('afterLoad');

      if ($.isFunction(callback)) {
        callback.call(that);
      }
    }

    if (typeof loader === 'string') {
      setContent(loader);
    } else if (typeof loader === 'object' && loader.hasOwnProperty('url')) {
      that.wizard.options.loading.show.call(that.wizard, that);

      $.ajax(loader.url, loader.settings || {}).done(data => {
        setContent(data);

        that.wizard.options.loading.hide.call(that.wizard, that);
      }).fail(() => {
        that.wizard.options.loading.fail.call(that.wizard, that);
      });
    } else {
      setContent('');
    }
  }

  trigger(event, ...args) {

    if ($.isArray(this.events[event])) {
      for (const i in this.events[event]) {
        if ({}.hasOwnProperty.call(this.events[event], i)) {
          this.events[event][i](...args);
        }
      }
    }

    this.wizard.trigger(...[event, this].concat(args));
  }

  enter(state) {
    this.states[state] = true;

    const classes = this.wizard.options.classes;
    this.$element.addClass(classes.step[state]);

    this.trigger('stateChange', true, state);
  }

  leave(state) {
    if (this.states[state]) {
      this.states[state] = false;

      const classes = this.wizard.options.classes;
      this.$element.removeClass(classes.step[state]);

      this.trigger('stateChange', false, state);
    }
  }

  setValidatorFromData() {
    const validator = this.$pane.data('validator');
    if (validator && $.isFunction(window[validator])) {
      this.validator = window[validator];
    }
  }

  setLoaderFromData() {
    const loader = this.$pane.data('loader');

    if (loader) {
      if ($.isFunction(window[loader])) {
        this.loader = window[loader];
      }
    } else {
      const url = this.$pane.data('loader-url');
      if (url) {
        this.loader = {
          url,
          settings: this.$pane.data('settings') || {}
        };
      }
    }
  }

  /*
   * Public methods below
   */
  active() {
    return this.wizard.goTo(this.index);
  }

  on(event, handler) {
    if ($.isFunction(handler)) {
      if ($.isArray(this.events[event])) {
        this.events[event].push(handler);
      } else {
        this.events[event] = [handler];
      }
    }

    return this;
  }

  off(event, handler) {
    if ($.isFunction(handler) && $.isArray(this.events[event])) {
      $.each(this.events[event], function (i, f) {
        /*eslint consistent-return: "off"*/
        if (f === handler) {
          delete this.events[event][i];
          return false;
        }
      });
    }

    return this;
  }

  is(state) {
    return this.states[state] && this.states[state] === true;
  }

  reset() {
    for (const state in this.states) {
      if ({}.hasOwnProperty.call(this.states, state)) {
        this.leave(state);
      }
    }
    this.setup();

    return this;
  }

  setLoader(loader) {
    this.loader = loader;

    if (this.is('active')) {
      this.load();
    }

    return this;
  }

  setValidator(validator) {
    if ($.isFunction(validator)) {
      this.validator = validator;
    }

    return this;
  }

  validate() {
    return this.validator.call(this.$pane.get(0), this);
  }
}

export default Step;
