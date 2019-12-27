/* eslint no-bitwise: "off" */
import NAMES from './names';
import * as util from './util';
import $ from 'jquery';

const hexNames = util.flip(NAMES);

export default {
  HSLtoRGB: function(hsl) {
    const h = hsl.h / 360;
    const s = hsl.s;
    const l = hsl.l;
    let m1;
    let m2;
    let rgb;
    if (l <= 0.5) {
      m2 = l * (s + 1);
    } else {
      m2 = l + s - (l * s);
    }
    m1 = l * 2 - m2;
    rgb = {
      r: this.hueToRGB(m1, m2, h + 1 / 3),
      g: this.hueToRGB(m1, m2, h),
      b: this.hueToRGB(m1, m2, h - 1 / 3)
    };
    if (typeof hsl.a !== 'undefined') {
      rgb.a = hsl.a;
    }
    if (hsl.l === 0) {
      rgb.h = hsl.h;
    }
    if (hsl.l === 1) {
      rgb.h = hsl.h;
    }
    return rgb;
  },

  hueToRGB: function(m1, m2, h) {
    let v;
    if (h < 0) {
      h += 1;
    } else if (h > 1) {
      h -= 1;
    }
    if ((h * 6) < 1) {
      v = m1 + (m2 - m1) * h * 6;
    } else if ((h * 2) < 1) {
      v = m2;
    } else if ((h * 3) < 2) {
      v = m1 + (m2 - m1) * (2 / 3 - h) * 6;
    } else {
      v = m1;
    }
    return Math.round(v * 255);
  },

  RGBtoHSL: function(rgb) {
    const r = rgb.r / 255;
    const g = rgb.g / 255;
    const b = rgb.b / 255;
    const min = Math.min(r, g, b);
    const max = Math.max(r, g, b);
    const diff = max - min;
    const add = max + min;
    const l = add * 0.5;
    let h;
    let s;

    if (min === max) {
      h = 0;
    } else if (r === max) {
      h = (60 * (g - b) / diff) + 360;
    } else if (g === max) {
      h = (60 * (b - r) / diff) + 120;
    } else {
      h = (60 * (r - g) / diff) + 240;
    }
    if (diff === 0) {
      s = 0;
    } else if (l <= 0.5) {
      s = diff / add;
    } else {
      s = diff / (2 - add);
    }

    return {
      h: Math.round(h) % 360,
      s,
      l
    };
  },

  RGBtoHEX: function(rgb) {
    let hex = [rgb.r.toString(16), rgb.g.toString(16), rgb.b.toString(16)];

    $.each(hex, (nr, val) => {
      if (val.length === 1) {
        hex[nr] = `0${val}`;
      }
    });
    return `#${hex.join('')}`;
  },

  HSLtoHEX: function(hsl) {
    const rgb = this.HSLtoRGB(hsl);
    return this.RGBtoHEX(rgb);
  },

  HSVtoHEX: function(hsv) {
    const rgb = this.HSVtoRGB(hsv);
    return this.RGBtoHEX(rgb);
  },

  RGBtoHSV: function(rgb) {
    const r = rgb.r / 255;
    const g = rgb.g / 255;
    const b = rgb.b / 255;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h;
    let s;
    const v = max;
    const diff = max - min;
    s = (max === 0) ? 0 : diff / max;
    if (max === min) {
      h = 0;
    } else {
      switch (max) {
        case r: {
          h = (g - b) / diff + (g < b ? 6 : 0);
          break;
        }
        case g: {
          h = (b - r) / diff + 2;
          break;
        }
        case b: {
          h = (r - g) / diff + 4;
          break;
        }
        default: {
          break;
        }
      }
      h /= 6;
    }

    return {
      h: Math.round(h * 360),
      s,
      v
    };
  },

  HSVtoRGB: function(hsv) {
    let r;
    let g;
    let b;
    let h = (hsv.h % 360) / 60;
    const s = hsv.s;
    const v = hsv.v;
    const c = v * s;
    const x = c * (1 - Math.abs(h % 2 - 1));

    r = g = b = v - c;
    h = ~~h;

    r += [c, x, 0, 0, x, c][h];
    g += [x, c, c, x, 0, 0][h];
    b += [0, 0, x, c, c, x][h];

    let rgb = {
      r: Math.round(r * 255),
      g: Math.round(g * 255),
      b: Math.round(b * 255)
    };

    if (typeof hsv.a !== 'undefined') {
      rgb.a = hsv.a;
    }

    if (hsv.v === 0) {
      rgb.h = hsv.h;
    }

    if (hsv.v === 1 && hsv.s === 0) {
      rgb.h = hsv.h;
    }

    return rgb;
  },

  HEXtoRGB: function(hex) {
    if (hex.length === 4) {
      hex = util.expandHex(hex);
    }
    return {
      r: util.parseIntFromHex(hex.substr(1, 2)),
      g: util.parseIntFromHex(hex.substr(3, 2)),
      b: util.parseIntFromHex(hex.substr(5, 2))
    };
  },

  isNAME: function(string) {
    if (NAMES.hasOwnProperty(string)) {
      return true;
    }
    return false;
  },

  NAMEtoHEX: function(name) {
    if (NAMES.hasOwnProperty(name)) {
      return `#${NAMES[name]}`;
    }
    return null;
  },

  NAMEtoRGB: function(name) {
    const hex = this.NAMEtoHEX(name);

    if (hex) {
      return this.HEXtoRGB(hex);
    }
    return null;
  },

  hasNAME: function(rgb) {
    let hex = this.RGBtoHEX(rgb);

    hex = util.shrinkHex(hex);

    if (hex.indexOf('#') === 0) {
      hex = hex.substr(1);
    }

    if (hexNames.hasOwnProperty(hex)) {
      return hexNames[hex];
    }
    return false;
  },

  RGBtoNAME: function(rgb) {
    const hasName = this.hasNAME(rgb);
    if (hasName) {
      return hasName;
    }

    return null;
  }
};
