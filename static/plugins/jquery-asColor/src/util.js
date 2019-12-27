export function expandHex(hex) {
  if (hex.indexOf('#') === 0) {
    hex = hex.substr(1);
  }
  if (!hex) {
    return null;
  }
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
  }
  return hex.length === 6 ? `#${hex}` : null;
}

export function shrinkHex(hex) {
  if (hex.indexOf('#') === 0) {
    hex = hex.substr(1);
  }
  if (hex.length === 6 && hex[0] === hex[1] && hex[2] === hex[3] && hex[4] === hex[5]) {
    hex = hex[0] + hex[2] + hex[4];
  }
  return `#${hex}`;
}

export function parseIntFromHex(val) {
  return parseInt(val, 16);
}

export function isPercentage(n) {
  return typeof n === 'string' && n.indexOf('%') === n.length - 1;
}

export function conventPercentageToRgb(n) {
  return parseInt(Math.round(n.slice(0, -1) * 2.55), 10);
}

export function convertPercentageToFloat(n) {
  return parseFloat(n.slice(0, -1) / 100, 10);
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
