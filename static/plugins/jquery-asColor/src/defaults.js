export default {
  format: false,
  shortenHex: false,
  hexUseName: false,
  reduceAlpha: false,
  alphaConvert: { // or false will disable convert
    'RGB': 'RGBA',
    'HSL': 'HSLA',
    'HEX': 'RGBA',
    'NAMESPACE': 'RGBA',
  },
  nameDegradation: 'HEX',
  invalidValue: '',
  zeroAlphaAsTransparent: true
};
