# [jQuery asColor](https://github.com/amazingSurge/jquery-asColor) ![bower][bower-image] [![NPM version][npm-image]][npm-url] [![Dependency Status][daviddm-image]][daviddm-url] [![prs-welcome]](#contributing)

> A jquery plugin used to parse css color string and convent it to other color formats. It support rgb, rgba, hex, hsl, hsla.

## Table of contents
- [Main files](#main-files)
- [Quick start](#quick-start)
- [Requirements](#requirements)
- [Usage](#usage)
- [Examples](#examples)
- [Options](#options)
- [Methods](#methods)
- [No conflict](#no-conflict)
- [Browser support](#browser-support)
- [Contributing](#contributing)
- [Development](#development)
- [Changelog](#changelog)
- [Copyright and license](#copyright-and-license)

## Main files
```
dist/
├── jquery-asColor.js
├── jquery-asColor.es.js
└── jquery-asColor.min.js
```

## Quick start
Several quick start options are available:
#### Download the latest build

 * [Development](https://raw.githubusercontent.com/amazingSurge/jquery-asColor/master/dist/jquery-asColor.js) - unminified
 * [Production](https://raw.githubusercontent.com/amazingSurge/jquery-asColor/master/dist/jquery-asColor.min.js) - minified

#### Install From Bower
```sh
bower install jquery-asColor --save
```

#### Install From Npm
```sh
npm install jquery-asColor --save
```

#### Install From Yarn
```sh
yarn add jquery-asColor
```

#### Build From Source
If you want build from source:

```sh
git clone git@github.com:amazingSurge/jquery-asColor.git
cd jquery-asColor
npm install
npm install -g gulp-cli babel-cli
gulp build
```

Done!

## Requirements
`jquery-asColor` requires the latest version of [`jQuery`](https://jquery.com/download/).

## Usage
#### Including files:

```html
<script src="/path/to/jquery.js"></script>
<script src="/path/to/jquery-asColor.js"></script>
```

#### Initialization
All you need to do is call the plugin on the element:

```javascript
jQuery(function($) {
  var color = $.asColor('rgba(255, 255, 255, 1)', {
    format: 'rgba',
    shortenHex: false,
    hexUseName: false,
    reduceAlpha: false,
    nameDegradation: 'HEX',
    invalidValue: '',
    zeroAlphaAsTransparent: true
  });
  var string = color.toString(), // rgba(255, 255, 255, 1)
    hex = color.toHEX(), // #ffffff
    rgb = color.toRGB(), // rgb(255, 255, 255)
    hsl = color.toHSL(), // hsl(0, 0%, 100%)
    hsla = color.toHSLA(), // hsla(0, 0%, 100%, 1)
    name = color.toNAME(); // white

  color.val('#000');
  color.format('hsla');
  color.alpha(0.5);
  var value = color.val(); // hsla(0, 0%, 0%, 0.5)
});
```

## Examples
There are some example usages that you can look at to get started. They can be found in the
[examples folder](https://github.com/amazingSurge/jquery-asColor/tree/master/examples).

## Options
`jquery-asColor` can accept an options object to alter the way it behaves. You can see the default options by call `$.asColor.setDefaults()`. The structure of an options object is as follows:

```
{
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
}
```

## Methods
Methods are called on asColor instances through the asColor method itself.
You can also save the instances to variable for further use.

#### toString()
Return the color string.
```javascript
color.toString();
```

#### format()
Get the color format or set the color format.
```javascript
color.format();
color.format('rgb');
```

#### val()
Set or get the color value.
```javascript
// get the val
color.val();

// set the val
color.val('rgb(66, 50, 50)');
```

#### set()
Set the color.
```javascript
color.set({
  r: 255,
  g: 255,
  b: 255,
  a: 0.5
});
```

#### get()
Get the color.
```javascript
var rgb = color.get();
```

#### alpha()
Get alpha.
```javascript
var alpha = color.alpha();
```

#### isValid()
Check color is valid.
```javascript
color.isValid();
```

#### toRGB()
Convent to rgb color.
```javascript
color.toRGB();
```

#### toRGBA()
Convent to rgba color.
```javascript
color.toRGBA();
```

#### toHEX()
Convent to hex color.
```javascript
color.toHEX();
```

#### toHSL()
Convent to hsl color.
```javascript
color.toHSL();
```

#### toHSLA()
Convent to hsla color.
```javascript
color.toHSLA();
```

## No conflict
If you have to use other plugin with the same namespace, just call the `$.asColor.noConflict` method to revert to it.

```html
<script src="other-plugin.js"></script>
<script src="jquery-asColor.js"></script>
<script>
  $.asColor.noConflict();
  // Code that uses other plugin's "$().asColor" can follow here.
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
review the [guidelines for contributing](CONTRIBUTING.md). Make sure you're using the latest version of `jquery-asColor` before submitting an issue. There are several ways to help out:

* [Bug reports](CONTRIBUTING.md#bug-reports)
* [Feature requests](CONTRIBUTING.md#feature-requests)
* [Pull requests](CONTRIBUTING.md#pull-requests)
* Write test cases for open bug issues
* Contribute to the documentation

## Development
`jquery-asColor` is built modularly and uses Gulp as a build system to build its distributable files. To install the necessary dependencies for the build system, please run:

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
To see the list of recent changes, see [Releases section](https://github.com/amazingSurge/jquery-asColor/releases).

## Copyright and license
Copyright (C) 2016 amazingSurge.

Licensed under [the LGPL license](LICENSE).

[⬆ back to top](#table-of-contents)

[bower-image]: https://img.shields.io/bower/v/jquery-asColor.svg?style=flat
[bower-link]: https://david-dm.org/amazingSurge/jquery-asColor/dev-status.svg
[npm-image]: https://badge.fury.io/js/jquery-asColor.svg?style=flat
[npm-url]: https://npmjs.org/package/jquery-asColor
[license]: https://img.shields.io/npm/l/jquery-asColor.svg?style=flat
[prs-welcome]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
[daviddm-image]: https://david-dm.org/amazingSurge/jquery-asColor.svg?style=flat
[daviddm-url]: https://david-dm.org/amazingSurge/jquery-asColor