/* eslint no-extend-native: "off" */
if (!String.prototype.includes) {
  String.prototype.includes = function(search, start) {
    'use strict';
    if (typeof start !== 'number') {
      start = 0;
    }

    if (start + search.length > this.length) {
      return false;
    }
    return this.indexOf(search, start) !== -1;
  };
}

export function getPrefix() {
  const ua = window.navigator.userAgent;
  let prefix = '';
  if (/MSIE/g.test(ua)) {
    prefix = '-ms-';
  } else if (/Firefox/g.test(ua)) {
    prefix = '-moz-';
  } else if (/(WebKit)/i.test(ua)) {
    prefix = '-webkit-';
  } else if (/Opera/g.test(ua)) {
    prefix = '-o-';
  }
  return prefix;
}

export function flip(o) {
  const flipped = {};
  for (const i in o) {
    if (o.hasOwnProperty(i)) {
      flipped[o[i]] = i;
    }
  }
  return flipped;
}

export function reverseDirection(direction) {
  const mapping = {
    'top': 'bottom',
    'right': 'left',
    'bottom': 'top',
    'left': 'right',
    'right top': 'left bottom',
    'top right': 'bottom left',
    'bottom right': 'top left',
    'right bottom': 'left top',
    'left bottom': 'right top',
    'bottom left': 'top right',
    'top left': 'bottom right',
    'left top': 'right bottom'
  };
  return mapping.hasOwnProperty(direction) ? mapping[direction] : direction;
}

export function isDirection(n) {
  const reg = /^(top|left|right|bottom)$/i;
  return reg.test(n);
}
