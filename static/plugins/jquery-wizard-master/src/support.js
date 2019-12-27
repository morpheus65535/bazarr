/**
 * Css features detect
 **/
import $ from "jquery";

let support = {};

((support) => {
  /**
   * Borrowed from Owl carousel
   **/
  const events = {
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
    style = $('<support>').get(0).style,
    tests = {
      csstransitions() {
        return Boolean(test('transition'));
      },
      cssanimations() {
        return Boolean(test('animation'));
      }
    };

  const test = (property, prefixed) => {
    let result = false,
      upper = property.charAt(0).toUpperCase() + property.slice(1);

    if (style[property] !== undefined) {
      result = property;
    }
    if (!result) {
      $.each(prefixes, (i, prefix) => {
        if (style[prefix + upper] !== undefined) {
          result = `-${prefix.toLowerCase()}-${upper}`;
          return false;
        }
        return true;
      });
    }

    if (prefixed) {
      return result;
    }
    if (result) {
      return true;
    }
    return false;
  };

  const prefixed = (property) => {
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

export default support;
