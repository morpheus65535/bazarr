/**
* jQuery wizard v0.4.3
* https://github.com/amazingSurge/jquery-wizard
*
* Copyright (c) amazingSurge
* Released under the LGPL-3.0 license
*/
(function(global, factory) {
  if (typeof define === "function" && define.amd) {
    define(['jquery'], factory);
  } else if (typeof exports !== "undefined") {
    factory(require('jquery'));
  } else {
    var mod = {
      exports: {}
    };
    factory(global.jQuery);
    global.jqueryWizardEs = mod.exports;
  }
})(this,

  function(_jquery) {
    'use strict';

    var _jquery2 = _interopRequireDefault(_jquery);

    function _interopRequireDefault(obj) {
      return obj && obj.__esModule ? obj : {
        default: obj
      };
    }

    function _toConsumableArray(arr) {
      if (Array.isArray(arr)) {

        for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) {
          arr2[i] = arr[i];
        }

        return arr2;
      } else {

        return Array.from(arr);
      }
    }

    var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ?

      function(obj) {
        return typeof obj;
      }
      :

      function(obj) {
        return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj;
      };

    function _classCallCheck(instance, Constructor) {
      if (!(instance instanceof Constructor)) {
        throw new TypeError("Cannot call a class as a function");
      }
    }

    var _createClass = function() {
      function defineProperties(target, props) {
        for (var i = 0; i < props.length; i++) {
          var descriptor = props[i];
          descriptor.enumerable = descriptor.enumerable || false;
          descriptor.configurable = true;

          if ("value" in descriptor)
            descriptor.writable = true;
          Object.defineProperty(target, descriptor.key, descriptor);
        }
      }

      return function(Constructor, protoProps, staticProps) {
        if (protoProps)
          defineProperties(Constructor.prototype, protoProps);

        if (staticProps)
          defineProperties(Constructor, staticProps);

        return Constructor;
      };
    }();

    /*eslint no-unused-vars: "off"*/
    /*eslint no-empty-function: "off"*/
    var DEFAULTS = {
      step: '.wizard-steps > li',

      getPane: function getPane(index, step) {
        return this.$element.find('.wizard-content').children().eq(index);
      },

      buttonsAppendTo: 'this',
      templates: {
        buttons: function buttons() {
          var options = this.options;

          return '<div class="wizard-buttons"><a class="wizard-back" href="#' + this.id + '" data-wizard="back" role="button">' + options.buttonLabels.back + '</a><a class="wizard-next" href="#' + this.id + '" data-wizard="next" role="button">' + options.buttonLabels.next + '</a><a class="wizard-finish" href="#' + this.id + '" data-wizard="finish" role="button">' + options.buttonLabels.finish + '</a></div>';
        }
      },

      classes: {
        step: {
          done: 'done',
          error: 'error',
          active: 'current',
          disabled: 'disabled',
          activing: 'activing',
          loading: 'loading'
        },

        pane: {
          active: 'active',
          activing: 'activing'
        },

        button: {
          hide: 'hide',
          disabled: 'disabled'
        }
      },

      autoFocus: true,
      keyboard: true,

      enableWhenVisited: false,

      buttonLabels: {
        next: 'Next',
        back: 'Back',
        finish: 'Finish'
      },

      loading: {
        show: function show(step) {},
        hide: function hide(step) {},
        fail: function fail(step) {}
      },

      cacheContent: false,

      validator: function validator(step) {
        return true;
      },

      onInit: null,
      onNext: null,
      onBack: null,
      onReset: null,

      onBeforeShow: null,
      onAfterShow: null,
      onBeforeHide: null,
      onAfterHide: null,
      onBeforeLoad: null,
      onAfterLoad: null,

      onBeforeChange: null,
      onAfterChange: null,

      onStateChange: null,

      onFinish: null
    };

    /**
     * Css features detect
     **/
    var support = {};

    (function(support) {
      /**
       * Borrowed from Owl carousel
       **/
      var events = {
          transition: {
            end: {
              WebkitTransition: 'webkitTransitionEnd',
              MozTransition: 'transitionend',
              OTransition: 'oTransitionEnd',
              transition: 'transitionend'
            }
          },
          animation: {
            end: {
              WebkitAnimation: 'webkitAnimationEnd',
              MozAnimation: 'animationend',
              OAnimation: 'oAnimationEnd',
              animation: 'animationend'
            }
          }
        },
        prefixes = ['webkit', 'Moz', 'O', 'ms'],
        style = (0, _jquery2.default)('<support>').get(0).style,
        tests = {
          csstransitions: function csstransitions() {
            return Boolean(test('transition'));
          },
          cssanimations: function cssanimations() {
            return Boolean(test('animation'));
          }
        };

      var test = function test(property, prefixed) {
        var result = false,
          upper = property.charAt(0).toUpperCase() + property.slice(1);

        if (style[property] !== undefined) {
          result = property;
        }

        if (!result) {
          _jquery2.default.each(prefixes,

            function(i, prefix) {
              if (style[prefix + upper] !== undefined) {
                result = '-' + prefix.toLowerCase() + '-' + upper;

                return false;
              }

              return true;
            }
          );
        }

        if (prefixed) {

          return result;
        }

        if (result) {

          return true;
        }

        return false;
      };

      var prefixed = function prefixed(property) {
        return test(property, true);
      };

      if (tests.csstransitions()) {
        /*eslint no-new-wrappers: "off"*/
        support.transition = new String(prefixed('transition'));
        support.transition.end = events.transition.end[support.transition];
      }

      if (tests.cssanimations()) {
        /*eslint no-new-wrappers: "off"*/
        support.animation = new String(prefixed('animation'));
        support.animation.end = events.animation.end[support.animation];
      }
    })(support);

    function emulateTransitionEnd($el, duration) {
      'use strict';

      var called = false;

      $el.one(support.transition.end,

        function() {
          called = true;
        }
      );
      var callback = function callback() {
        if (!called) {
          $el.trigger(support.transition.end);
        }
      };
      setTimeout(callback, duration);
    }

    var Step = function() {
      function Step(element, wizard, index) {
        _classCallCheck(this, Step);

        this.TRANSITION_DURATION = 200;

        this.initialize(element, wizard, index);
      }

      _createClass(Step, [{
        key: 'initialize',
        value: function initialize(element, wizard, index) {
          this.$element = (0, _jquery2.default)(element);
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
      }, {
        key: 'getPaneFromTarget',
        value: function getPaneFromTarget() {
          var selector = this.$element.data('target');

          if (!selector) {
            selector = this.$element.attr('href');
            selector = selector && selector.replace(/.*(?=#[^\s]*$)/, '');
          }

          if (selector) {

            return (0, _jquery2.default)(selector);
          }

          return null;
        }
      }, {
        key: 'setup',
        value: function setup() {
          var current = this.wizard.currentIndex();

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

          var classes = this.wizard.options.classes;

          if (this.is('active')) {
            this.$pane.addClass(classes.pane.active);
          } else {
            this.$pane.removeClass(classes.pane.active);
          }
        }
      }, {
        key: 'show',
        value: function show(callback) {
          if (this.is('activing') || this.is('active')) {

            return;
          }

          this.trigger('beforeShow');
          this.enter('activing');

          var classes = this.wizard.options.classes;

          this.$element.attr('aria-expanded', true);

          this.$pane.addClass(classes.pane.activing).addClass(classes.pane.active).attr('aria-expanded', true);

          var complete = function complete() {
            this.$pane.removeClass(classes.pane.activing);

            this.leave('activing');
            this.enter('active');
            this.trigger('afterShow');

            if (_jquery2.default.isFunction(callback)) {
              callback.call(this);
            }
          };

          if (!support.transition) {
            complete.call(this);

            return;
          }

          this.$pane.one(support.transition.end, _jquery2.default.proxy(complete, this));

          emulateTransitionEnd(this.$pane, this.TRANSITION_DURATION);
        }
      }, {
        key: 'hide',
        value: function hide(callback) {
          if (this.is('activing') || !this.is('active')) {

            return;
          }

          this.trigger('beforeHide');
          this.enter('activing');

          var classes = this.wizard.options.classes;

          this.$element.attr('aria-expanded', false);

          this.$pane.addClass(classes.pane.activing).removeClass(classes.pane.active).attr('aria-expanded', false);

          var complete = function complete() {
            this.$pane.removeClass(classes.pane.activing);

            this.leave('activing');
            this.leave('active');
            this.trigger('afterHide');

            if (_jquery2.default.isFunction(callback)) {
              callback.call(this);
            }
          };

          if (!support.transition) {
            complete.call(this);

            return;
          }

          this.$pane.one(support.transition.end, _jquery2.default.proxy(complete, this));

          emulateTransitionEnd(this.$pane, this.TRANSITION_DURATION);
        }
      }, {
        key: 'empty',
        value: function empty() {
          this.$pane.empty();
        }
      }, {
        key: 'load',
        value: function load(callback) {
          var that = this;
          var loader = this.loader;

          if (_jquery2.default.isFunction(loader)) {
            loader = loader.call(this.wizard, this);
          }

          if (this.wizard.options.cacheContent && this.loaded) {

            if (_jquery2.default.isFunction(callback)) {
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

            if (_jquery2.default.isFunction(callback)) {
              callback.call(that);
            }
          }

          if (typeof loader === 'string') {
            setContent(loader);
          } else if ((typeof loader === 'undefined' ? 'undefined' : _typeof(loader)) === 'object' && loader.hasOwnProperty('url')) {
            that.wizard.options.loading.show.call(that.wizard, that);

            _jquery2.default.ajax(loader.url, loader.settings || {}).done(

              function(data) {
                setContent(data);

                that.wizard.options.loading.hide.call(that.wizard, that);
              }
            ).fail(

              function() {
                that.wizard.options.loading.fail.call(that.wizard, that);
              }
            );
          } else {
            setContent('');
          }
        }
      }, {
        key: 'trigger',
        value: function trigger(event) {
          var _wizard;

          for (var _len = arguments.length, args = Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
            args[_key - 1] = arguments[_key];
          }

          if (_jquery2.default.isArray(this.events[event])) {

            for (var i in this.events[event]) {

              if ({}.hasOwnProperty.call(this.events[event], i)) {
                var _events$event;

                (_events$event = this.events[event])[i].apply(_events$event, args);
              }
            }
          }

          (_wizard = this.wizard).trigger.apply(_wizard, _toConsumableArray([event, this].concat(args)));
        }
      }, {
        key: 'enter',
        value: function enter(state) {
          this.states[state] = true;

          var classes = this.wizard.options.classes;
          this.$element.addClass(classes.step[state]);

          this.trigger('stateChange', true, state);
        }
      }, {
        key: 'leave',
        value: function leave(state) {
          if (this.states[state]) {
            this.states[state] = false;

            var classes = this.wizard.options.classes;
            this.$element.removeClass(classes.step[state]);

            this.trigger('stateChange', false, state);
          }
        }
      }, {
        key: 'setValidatorFromData',
        value: function setValidatorFromData() {
          var validator = this.$pane.data('validator');

          if (validator && _jquery2.default.isFunction(window[validator])) {
            this.validator = window[validator];
          }
        }
      }, {
        key: 'setLoaderFromData',
        value: function setLoaderFromData() {
          var loader = this.$pane.data('loader');

          if (loader) {

            if (_jquery2.default.isFunction(window[loader])) {
              this.loader = window[loader];
            }
          } else {
            var url = this.$pane.data('loader-url');

            if (url) {
              this.loader = {
                url: url,
                settings: this.$pane.data('settings') || {}
              };
            }
          }
        }
      }, {
        key: 'active',
        value: function active() {
          return this.wizard.goTo(this.index);
        }
      }, {
        key: 'on',
        value: function on(event, handler) {
          if (_jquery2.default.isFunction(handler)) {

            if (_jquery2.default.isArray(this.events[event])) {
              this.events[event].push(handler);
            } else {
              this.events[event] = [handler];
            }
          }

          return this;
        }
      }, {
        key: 'off',
        value: function off(event, handler) {
          if (_jquery2.default.isFunction(handler) && _jquery2.default.isArray(this.events[event])) {
            _jquery2.default.each(this.events[event],

              function(i, f) {
                /*eslint consistent-return: "off"*/

                if (f === handler) {
                  delete this.events[event][i];

                  return false;
                }
              }
            );
          }

          return this;
        }
      }, {
        key: 'is',
        value: function is(state) {
          return this.states[state] && this.states[state] === true;
        }
      }, {
        key: 'reset',
        value: function reset() {
          for (var state in this.states) {

            if ({}.hasOwnProperty.call(this.states, state)) {
              this.leave(state);
            }
          }
          this.setup();

          return this;
        }
      }, {
        key: 'setLoader',
        value: function setLoader(loader) {
          this.loader = loader;

          if (this.is('active')) {
            this.load();
          }

          return this;
        }
      }, {
        key: 'setValidator',
        value: function setValidator(validator) {
          if (_jquery2.default.isFunction(validator)) {
            this.validator = validator;
          }

          return this;
        }
      }, {
        key: 'validate',
        value: function validate() {
          return this.validator.call(this.$pane.get(0), this);
        }
      }]);

      return Step;
    }();

    var counter = 0;
    var NAMESPACE$1 = 'wizard';

    var wizard = function() {
      function wizard(element) {
        var options = arguments.length <= 1 || arguments[1] === undefined ? {} : arguments[1];

        _classCallCheck(this, wizard);

        this.$element = (0, _jquery2.default)(element);

        this.options = _jquery2.default.extend(true, {}, DEFAULTS, options);

        this.$steps = this.$element.find(this.options.step);

        this.id = this.$element.attr('id');

        if (!this.id) {
          this.id = 'wizard-' + ++counter;
          this.$element.attr('id', this.id);
        }

        this.trigger('init');

        this.initialize();
      }

      _createClass(wizard, [{
        key: 'initialize',
        value: function initialize() {
          this.steps = [];
          var that = this;

          this.$steps.each(

            function(index) {
              that.steps.push(new Step(this, that, index));
            }
          );

          this._current = 0;
          this.transitioning = null;

          _jquery2.default.each(this.steps,

            function(i, step) {
              step.setup();
            }
          );

          this.setup();

          this.$element.on('click', this.options.step,

            function(e) {
              var index = (0, _jquery2.default)(this).data('wizard-index');

              if (!that.get(index).is('disabled')) {
                that.goTo(index);
              }

              e.preventDefault();
              e.stopPropagation();
            }
          );

          if (this.options.keyboard) {
            (0, _jquery2.default)(document).on('keyup', _jquery2.default.proxy(this.keydown, this));
          }

          this.trigger('ready');
        }
      }, {
        key: 'setup',
        value: function setup() {
          this.$buttons = (0, _jquery2.default)(this.options.templates.buttons.call(this));

          this.updateButtons();

          var buttonsAppendTo = this.options.buttonsAppendTo;
          var $to = void 0;

          if (buttonsAppendTo === 'this') {
            $to = this.$element;
          } else if (_jquery2.default.isFunction(buttonsAppendTo)) {
            $to = buttonsAppendTo.call(this);
          } else {
            $to = this.$element.find(buttonsAppendTo);
          }
          this.$buttons = this.$buttons.appendTo($to);
        }
      }, {
        key: 'updateButtons',
        value: function updateButtons() {
          var classes = this.options.classes.button;
          var $back = this.$buttons.find('[data-wizard="back"]');
          var $next = this.$buttons.find('[data-wizard="next"]');
          var $finish = this.$buttons.find('[data-wizard="finish"]');

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
      }, {
        key: 'updateSteps',
        value: function updateSteps() {
          var _this = this;

          _jquery2.default.each(this.steps,

            function(i, step) {
              if (i > _this._current) {
                step.leave('error');
                step.leave('active');
                step.leave('done');

                if (!_this.options.enableWhenVisited) {
                  step.enter('disabled');
                }
              }
            }
          );
        }
      }, {
        key: 'keydown',
        value: function keydown(e) {
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
      }, {
        key: 'trigger',
        value: function trigger(eventType) {
          for (var _len2 = arguments.length, params = Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
            params[_key2 - 1] = arguments[_key2];
          }

          var data = [this].concat(params);

          // event
          this.$element.trigger(NAMESPACE$1 + '::' + eventType, data);

          // callback
          eventType = eventType.replace(/\b\w+\b/g,

            function(word) {
              return word.substring(0, 1).toUpperCase() + word.substring(1);
            }
          );
          var onFunction = 'on' + eventType;

          if (typeof this.options[onFunction] === 'function') {
            this.options[onFunction].apply(this, params);
          }
        }
      }, {
        key: 'get',
        value: function get(index) {
          if (typeof index === 'string' && index.substring(0, 1) === '#') {
            var id = index.substring(1);

            for (var i in this.steps) {

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
      }, {
        key: 'goTo',
        value: function goTo(index, callback) {
          if (index === this._current || this.transitioning === true) {

            return false;
          }

          var current = this.current();
          var to = this.get(index);

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

          var that = this;
          var process = function process() {
            that.trigger('beforeChange', current, to);
            that.transitioning = true;

            current.hide();
            to.show(

              function() {
                that._current = index;
                that.transitioning = false;
                this.leave('disabled');

                that.updateButtons();
                that.updateSteps();

                if (that.options.autoFocus) {
                  var $input = this.$pane.find(':input');

                  if ($input.length > 0) {
                    $input.eq(0).focus();
                  } else {
                    this.$pane.focus();
                  }
                }

                if (_jquery2.default.isFunction(callback)) {
                  callback.call(that);
                }

                that.trigger('afterChange', current, to);
              }
            );
          };

          if (to.loader) {
            to.load(

              function() {
                process();
              }
            );
          } else {
            process();
          }

          return true;
        }
      }, {
        key: 'length',
        value: function length() {
          return this.steps.length;
        }
      }, {
        key: 'current',
        value: function current() {
          return this.get(this._current);
        }
      }, {
        key: 'currentIndex',
        value: function currentIndex() {
          return this._current;
        }
      }, {
        key: 'lastIndex',
        value: function lastIndex() {
          return this.length() - 1;
        }
      }, {
        key: 'next',
        value: function next() {
          var _this2 = this;

          if (this._current < this.lastIndex()) {
            (function() {
              var from = _this2._current,
                to = _this2._current + 1;

              _this2.goTo(to,

                function() {
                  this.trigger('next', this.get(from), this.get(to));
                }
              );
            })();
          }

          return false;
        }
      }, {
        key: 'back',
        value: function back() {
          var _this3 = this;

          if (this._current > 0) {
            (function() {
              var from = _this3._current,
                to = _this3._current - 1;

              _this3.goTo(to,

                function() {
                  this.trigger('back', this.get(from), this.get(to));
                }
              );
            })();
          }

          return false;
        }
      }, {
        key: 'first',
        value: function first() {
          return this.goTo(0);
        }
      }, {
        key: 'finish',
        value: function finish() {
          if (this._current === this.lastIndex()) {
            var current = this.current();

            if (current.validate()) {
              this.trigger('finish');
              current.leave('error');
              current.enter('done');
            } else {
              current.enter('error');
            }
          }
        }
      }, {
        key: 'reset',
        value: function reset() {
          this._current = 0;

          _jquery2.default.each(this.steps,

            function(i, step) {
              step.reset();
            }
          );

          this.trigger('reset');
        }
      }], [{
        key: 'setDefaults',
        value: function setDefaults(options) {
          _jquery2.default.extend(true, DEFAULTS, _jquery2.default.isPlainObject(options) && options);
        }
      }]);

      return wizard;
    }();

    (0, _jquery2.default)(document).on('click', '[data-wizard]',

      function(e) {
        'use strict';

        var href = void 0;
        var $this = (0, _jquery2.default)(this);
        var $target = (0, _jquery2.default)($this.attr('data-target') || (href = $this.attr('href')) && href.replace(/.*(?=#[^\s]+$)/, ''));

        var wizard = $target.data(NAMESPACE$1);

        if (!wizard) {

          return;
        }

        var method = $this.data(NAMESPACE$1);

        if (/^(back|next|first|finish|reset)$/.test(method)) {
          wizard[method]();
        }

        e.preventDefault();
      }
    );

    var info = {
      version: '0.4.3'
    };

    var NAMESPACE = 'wizard';
    var OtherWizard = _jquery2.default.fn.wizard;

    var jQueryWizard = function jQueryWizard(options) {
      var _this4 = this;

      for (var _len3 = arguments.length, args = Array(_len3 > 1 ? _len3 - 1 : 0), _key3 = 1; _key3 < _len3; _key3++) {
        args[_key3 - 1] = arguments[_key3];
      }

      if (typeof options === 'string') {
        var _ret3 = function() {
          var method = options;

          if (/^_/.test(method)) {

            return {
              v: false
            };
          } else if (/^(get)/.test(method)) {
            var instance = _this4.first().data(NAMESPACE);

            if (instance && typeof instance[method] === 'function') {

              return {
                v: instance[method].apply(instance, args)
              };
            }
          } else {

            return {
              v: _this4.each(

                function() {
                  var instance = _jquery2.default.data(this, NAMESPACE);

                  if (instance && typeof instance[method] === 'function') {
                    instance[method].apply(instance, args);
                  }
                }
              )
            };
          }
        }();

        if ((typeof _ret3 === 'undefined' ? 'undefined' : _typeof(_ret3)) === "object")

          return _ret3.v;
      }

      return this.each(

        function() {
          if (!(0, _jquery2.default)(this).data(NAMESPACE)) {
            (0, _jquery2.default)(this).data(NAMESPACE, new wizard(this, options));
          }
        }
      );
    };

    _jquery2.default.fn.wizard = jQueryWizard;

    _jquery2.default.wizard = _jquery2.default.extend({
      setDefaults: wizard.setDefaults,
      noConflict: function noConflict() {
        _jquery2.default.fn.wizard = OtherWizard;

        return jQueryWizard;
      }
    }, info);
  }
);