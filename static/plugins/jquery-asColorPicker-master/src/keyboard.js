// keyboard
import $ from 'jquery';

const $doc = $(document);
const keyboard = {
  keys: {
    'UP': 38,
    'DOWN': 40,
    'LEFT': 37,
    'RIGHT': 39,
    'RETURN': 13,
    'ESCAPE': 27,
    'BACKSPACE': 8,
    'SPACE': 32
  },
  map: {},
  bound: false,
  press(e) {
    const key = e.keyCode || e.which;
    if (key in keyboard.map && typeof keyboard.map[key] === 'function') {
      keyboard.map[key](e);
    }
    return false;
  },
  attach(map) {
    let key;
    let up;
    for (key in map) {
      if (map.hasOwnProperty(key)) {
        up = key.toUpperCase();
        if (up in keyboard.keys) {
          keyboard.map[keyboard.keys[up]] = map[key];
        } else {
          keyboard.map[up] = map[key];
        }
      }
    }
    if (!keyboard.bound) {
      keyboard.bound = true;
      $doc.bind('keydown', keyboard.press);
    }
  },
  detach() {
    keyboard.bound = false;
    keyboard.map = {};
    $doc.unbind('keydown', keyboard.press);
  }
};
$doc.on('asColorPicker::init', (event, instance) => {
  if (instance.options.keyboard === true) {
    instance._keyboard = keyboard;
  }
});
