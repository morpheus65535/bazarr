# [jQuery asColorPicker](https://github.com/amazingSurge/jquery-asColorPicker) ![bower][bower-image] [![NPM version][npm-image]][npm-url] [![Dependency Status][daviddm-image]][daviddm-url] [![prs-welcome]](#contributing)

> A jquery plugin that convent input into color picker.

## Table of contents
- [Main files](#main-files)
- [Quick start](#quick-start)
- [Requirements](#requirements)
- [Usage](#usage)
- [Examples](#examples)
- [Options](#options)
- [Methods](#methods)
- [Events](#events)
- [No conflict](#no-conflict)
- [Browser support](#browser-support)
- [Contributing](#contributing)
- [Development](#development)
- [Changelog](#changelog)
- [Copyright and license](#copyright-and-license)

## Main files
```
dist/
├── jquery-asColorPicker.js
├── jquery-asColorPicker.es.js
├── jquery-asColorPicker.min.js
└── css/
    ├── asColorPicker.css
    └── asColorPicker.min.css
```

## Quick start
Several quick start options are available:
#### Download the latest build

 * [Development](https://raw.githubusercontent.com/amazingSurge/jquery-asColorPicker/master/dist/jquery-asColorPicker.js) - unminified
 * [Production](https://raw.githubusercontent.com/amazingSurge/jquery-asColorPicker/master/dist/jquery-asColorPicker.min.js) - minified

#### Install From Bower
```sh
bower install jquery-asColorPicker --save
```

#### Install From Npm
```sh
npm install jquery-asColorPicker --save
```

#### Install From Yarn
```sh
yarn add jquery-asColorPicker
```

#### Build From Source
If you want build from source:

```sh
git clone git@github.com:amazingSurge/jquery-asColorPicker.git
cd jquery-asColorPicker
npm install
npm install -g gulp-cli babel-cli
gulp build
```

Done!

## Requirements
`jquery-asColorPicker` requires the latest version of [`jQuery`](https://jquery.com/download/), [`jquery-asColor`](https://github.com/amazingSurge/jquery-asColor), and [`jquery-asGradient`](https://github.com/amazingSurge/jquery-asGradient).

## Usage
#### Including files:

```html
<link rel="stylesheet" href="/path/to/asColorPicker.css">
<script src="/path/to/jquery.js"></script>
<script src="/path/to/jquery-asColor.js"></script>
<script src="/path/to/jquery-asGradient.js"></script>
<script src="/path/to/jquery-asColorPicker.js"></script>
```

#### Required HTML structure

```html
<input type='text' class="example" value="#000" />
```

#### Initialization
All you need to do is call the plugin on the element:

```javascript
jQuery(function($) {
  $('.example').asColorPicker(); 
});
```

## Examples
There are some example usages that you can look at to get started. They can be found in the
[examples folder](https://github.com/amazingSurge/jquery-asColorPicker/tree/master/examples).

## Options
`jquery-asColorPicker` can accept an options object to alter the way it behaves. You can see the default options by call `$.asColorPicker.setDefaults()`. The structure of an options object is as follows:

```
{
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
}
```

## Methods
Methods are called on asColorPicker instances through the asColorPicker method itself.
You can also save the instances to variable for further use.

```javascript
// call directly
$().asColorPicker('destroy');

// or
var api = $().data('asColorPicker');
api.destroy();
```

#### opacity()
Get or set opacity.
```javascript
// get opacity
$().asColorPicker('opacity');

// set opacity
$().asColorPicker('opacity', 0.1);
```

#### open()
Show the colorpicker dropdown.
```javascript
$().asColorPicker('open');
```

#### close()
Close the colorpicker dropdown.
```javascript
$().asColorPicker('close');
```

#### clear()
Clear the colorpicker.
```javascript
$().asColorPicker('clear');
```

#### val(value)
Get or set the colorpicker val.
```javascript
// get the color
$().asColorPicker('val');

// set the color
$().asColorPicker('val', 'rgb(100, 100, 100)');
```

#### set(value)
Set the color.
```javascript
$().asColorPicker('set', 'rgb(100, 100, 100)');
```

#### get()
Get the color.
```javascript
$().asColorPicker('get');
```

#### enable()
Enable the colorpicker functions.
```javascript
$().asColorPicker('enable');
```

#### enable()
Enable the colorpicker functions.
```javascript
$().asColorPicker('enable');
```

#### disable()
Disable the colorpicker functions.
```javascript
$().asColorPicker('disable');
```

#### destroy()
Destroy the colorpicker instance.
```javascript
$().asColorPicker('destroy');
```

## Events
`jquery-asColorPicker` provides custom events for the plugin’s unique actions. 

```javascript
$('.the-element').on('asColorPicker::change', function (e) {
  // on value change 
});

```

Event   | Description
------- | -----------
init    | Fires when the instance is setup for the first time.
ready   | Fires when the instance is ready for API use.
change  | Fires when the value changed. 
enable  | Fires when the `enable` instance method has been called.
disable | Fires when the `disable` instance method has been called.
destroy | Fires when an instance is destroyed. 

## No conflict
If you have to use other plugin with the same namespace, just call the `$.asColorPicker.noConflict` method to revert to it.

```html
<script src="other-plugin.js"></script>
<script src="jquery-asColorPicker.js"></script>
<script>
  $.asColorPicker.noConflict();
  // Code that uses other plugin's "$().asColorPicker" can follow here.
</script>
```

## Browser support

Tested on all major browsers.

| <img src="https://raw.githubusercontent.com/alrra/browser-logos/master/safari/safari_32x32.png" alt="Safari"> | <img src="https://raw.githubusercontent.com/alrra/browser-logos/master/chrome/chrome_32x32.png" alt="Chrome"> | <img src="https://raw.githubusercontent.com/alrra/browser-logos/master/firefox/firefox_32x32.png" alt="Firefox"> | <img src="https://raw.githubusercontent.com/alrra/browser-logos/master/edge/edge_32x32.png" alt="Edge"> | <img src="https://raw.githubusercontent.com/alrra/browser-logos/master/internet-explorer/internet-explorer_32x32.png" alt="IE"> | <img src="https://raw.githubusercontent.com/alrra/browser-logos/master/opera/opera_32x32.png" alt="Opera"> |
|:--:|:--:|:--:|:--:|:--:|:--:|
| Latest ✓ | Latest ✓ | Latest ✓ | Latest ✓ | 9-11 ✓ | Latest ✓ |

As a jQuery plugin, you also need to see the [jQuery Browser Support](http://jquery.com/browser-support/).

## Contributing
Anyone and everyone is welcome to contribute. Please take a moment to
review the [guidelines for contributing](CONTRIBUTING.md). Make sure you're using the latest version of `jquery-asColorPicker` before submitting an issue. There are several ways to help out:

* [Bug reports](CONTRIBUTING.md#bug-reports)
* [Feature requests](CONTRIBUTING.md#feature-requests)
* [Pull requests](CONTRIBUTING.md#pull-requests)
* Write test cases for open bug issues
* Contribute to the documentation

## Development
`jquery-asColorPicker` is built modularly and uses Gulp as a build system to build its distributable files. To install the necessary dependencies for the build system, please run:

```sh
npm install -g gulp
npm install -g babel-cli
npm install
```

Then you can generate new distributable files from the sources, using:
```
gulp build
```

More gulp tasks can be found [here](CONTRIBUTING.md#available-tasks).

## Changelog
To see the list of recent changes, see [Releases section](https://github.com/amazingSurge/jquery-asColorPicker/releases).

## Copyright and license
Copyright (C) 2016 amazingSurge.

Licensed under [the LGPL license](LICENSE).

[⬆ back to top](#table-of-contents)

[bower-image]: https://img.shields.io/bower/v/jquery-asColorPicker.svg?style=flat
[bower-link]: https://david-dm.org/amazingSurge/jquery-asColorPicker/dev-status.svg
[npm-image]: https://badge.fury.io/js/jquery-asColorPicker.svg?style=flat
[npm-url]: https://npmjs.org/package/jquery-asColorPicker
[license]: https://img.shields.io/npm/l/jquery-asColorPicker.svg?style=flat
[prs-welcome]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
[daviddm-image]: https://david-dm.org/amazingSurge/jquery-asColorPicker.svg?style=flat
[daviddm-url]: https://david-dm.org/amazingSurge/jquery-asColorPicker