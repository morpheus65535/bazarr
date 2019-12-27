import $ from 'jquery';
import DEFAULTS from './defaults';
import Step from './step';

let counter = 0;
const NAMESPACE = 'wizard';

class wizard {
  constructor(element, options = {}) {
    this.$element = $(element);

    this.options = $.extend(true, {}, DEFAULTS, options);

    this.$steps = this.$element.find(this.options.step);

    this.id = this.$element.attr('id');
    if (!this.id) {
      this.id = `wizard-${++counter}`;
      this.$element.attr('id', this.id);
    }

    this.trigger('init');

    this.initialize();
  }

  initialize() {
    this.steps = [];
    const that = this;

    this.$steps.each(function (index) {
      that.steps.push(new Step(this, that, index));
    });

    this._current = 0;
    this.transitioning = null;

    $.each(this.steps, (i, step) => {
      step.setup();
    });

    this.setup();

    this.$element.on('click', this.options.step, function (e) {
      const index = $(this).data('wizard-index');

      if (!that.get(index).is('disabled')) {
        that.goTo(index);
      }

      e.preventDefault();
      e.stopPropagation();
    });

    if (this.options.keyboard) {
      $(document).on('keyup', $.proxy(this.keydown, this));
    }

    this.trigger('ready');
  }

  setup() {
    this.$buttons = $(this.options.templates.buttons.call(this));

    this.updateButtons();

    const buttonsAppendTo = this.options.buttonsAppendTo;
    let $to;
    if (buttonsAppendTo === 'this') {
      $to = this.$element;
    } else if ($.isFunction(buttonsAppendTo)) {
      $to = buttonsAppendTo.call(this);
    } else {
      $to = this.$element.find(buttonsAppendTo);
    }
    this.$buttons = this.$buttons.appendTo($to);
  }

  updateButtons() {
    const classes = this.options.classes.button;
    const $back = this.$buttons.find('[data-wizard="back"]');
    const $next = this.$buttons.find('[data-wizard="next"]');
    const $finish = this.$buttons.find('[data-wizard="finish"]');

    if (this._current === 0) {
      $back.addClass(classes.disabled);
    } else {
      $back.removeClass(classes.disabled);
    }

    if (this._current === this.lastIndex()) {
      $next.addClass(classes.hide);
      $finish.removeClass(classes.hide);
    } else {
      $next.removeClass(classes.hide);
      $finish.addClass(classes.hide);
    }
  }

  updateSteps() {
    $.each(this.steps, (i, step) => {
      if (i > this._current) {
        step.leave('error');
        step.leave('active');
        step.leave('done');

        if (!this.options.enableWhenVisited) {
          step.enter('disabled');
        }
      }
    });
  }

  keydown(e) {
    if (/input|textarea/i.test(e.target.tagName)) {
      return;
    }

    switch (e.which) {
      case 37:
        this.back();
        break;
      case 39:
        this.next();
        break;
      default:
        return;
    }

    e.preventDefault();
  }

  trigger(eventType, ...params) {
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

  get(index) {
    if (typeof index === 'string' && index.substring(0, 1) === '#') {
      const id = index.substring(1);
      for (const i in this.steps) {
        if (this.steps[i].$pane.attr('id') === id) {
          return this.steps[i];
        }
      }
    }

    if (index < this.length() && this.steps[index]) {
      return this.steps[index];
    }

    return null;
  }

  goTo(index, callback) {
    if (index === this._current || this.transitioning === true) {
      return false;
    }

    const current = this.current();
    const to = this.get(index);

    if (index > this._current) {
      if (!current.validate()) {
        current.leave('done');
        current.enter('error');

        return -1;
      }
      current.leave('error');

      if (index > this._current) {
        current.enter('done');
      }
    }

    const that = this;
    const process = () => {
      that.trigger('beforeChange', current, to);
      that.transitioning = true;

      current.hide();
      to.show(function () {
        that._current = index;
        that.transitioning = false;
        this.leave('disabled');

        that.updateButtons();
        that.updateSteps();

        if (that.options.autoFocus) {
          const $input = this.$pane.find(':input');
          if ($input.length > 0) {
            $input.eq(0).focus();
          } else {
            this.$pane.focus();
          }
        }

        if ($.isFunction(callback)) {
          callback.call(that);
        }

        that.trigger('afterChange', current, to);
      });
    };

    if (to.loader) {
      to.load(() => {
        process();
      });
    } else {
      process();
    }

    return true;
  }

  length() {
    return this.steps.length;
  }

  current() {
    return this.get(this._current);
  }

  currentIndex() {
    return this._current;
  }

  lastIndex() {
    return this.length() - 1;
  }

  next() {
    if (this._current < this.lastIndex()) {
      const from = this._current,
        to = this._current + 1;

      this.goTo(to, function () {
        this.trigger('next', this.get(from), this.get(to));
      });
    }

    return false;
  }

  back() {
    if (this._current > 0) {
      const from = this._current,
        to = this._current - 1;

      this.goTo(to, function () {
        this.trigger('back', this.get(from), this.get(to));
      });
    }

    return false;
  }

  first() {
    return this.goTo(0);
  }

  finish() {
    if (this._current === this.lastIndex()) {
      const current = this.current();
      if (current.validate()) {
        this.trigger('finish');
        current.leave('error');
        current.enter('done');
      } else {
        current.enter('error');
      }
    }
  }

  reset() {
    this._current = 0;

    $.each(this.steps, (i, step) => {
      step.reset();
    });

    this.trigger('reset');
  }

  static setDefaults(options) {
    $.extend(true, DEFAULTS, $.isPlainObject(options) && options);
  }
}

$(document).on('click', '[data-wizard]', function (e) {
  'use strict';
  let href;
  const $this = $(this);
  const $target = $($this.attr('data-target') || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, ''));

  const wizard = $target.data(NAMESPACE);

  if (!wizard) {
    return;
  }

  const method = $this.data(NAMESPACE);

  if (/^(back|next|first|finish|reset)$/.test(method)) {
    wizard[method]();
  }

  e.preventDefault();
});

export default wizard;
