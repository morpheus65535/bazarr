export default {
  namespace: 'asColorPicker',
  readonly: false,
  skin: null,
  lang: 'en',
  hideInput: false,
  hideFireChange: true,
  keyboard: false,
  color: {
    format: false,
    alphaConvert: { // or false will disable convert
      'RGB': 'RGBA',
      'HSL': 'HSLA',
      'HEX': 'RGBA',
      'NAMESPACE': 'RGBA',
    },
    shortenHex: false,
    hexUseName: false,
    reduceAlpha: true,
    nameDegradation: 'HEX',
    invalidValue: '',
    zeroAlphaAsTransparent: true
  },
  mode: 'simple',
  onInit: null,
  onReady: null,
  onChange: null,
  onClose: null,
  onOpen: null,
  onApply: null
};
