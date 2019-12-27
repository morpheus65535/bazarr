export default {
  prefixes: ['-webkit-', '-moz-', '-ms-', '-o-'],
  forceStandard: true,
  angleUseKeyword: true,
  emptyString: '',
  degradationFormat: false,
  cleanPosition: true,
  color: {
    format: false, // rgb, rgba, hsl, hsla, hex
    hexUseName: false,
    reduceAlpha: true,
    shortenHex: true,
    zeroAlphaAsTransparent: false,
    invalidValue: {
      r: 0,
      g: 0,
      b: 0,
      a: 1
    }
  }
};
