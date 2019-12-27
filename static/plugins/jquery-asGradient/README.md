# [jQuery asGradient](https://github.com/amazingSurge/jquery-asGradient) ![bower][bower-image] [![NPM version][npm-image]][npm-url] [![Dependency Status][daviddm-image]][daviddm-url] [![prs-welcome]](#contributing)

> A jquery plugin used to manipulate css image gradient. You can add a new color stop. Change the position of color stop. Or remove a color stop. In the end, it can output a formated standard css gradient string. 

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
├── jquery-asGradient.js
├── jquery-asGradient.es.js
└── jquery-asGradient.min.js
```

## Quick start
Several quick start options are available:
#### Download the latest build

 * [Development](https://raw.githubusercontent.com/amazingSurge/jquery-asGradient/master/dist/jquery-asGradient.js) - unminified
 * [Production](https://raw.githubusercontent.com/amazingSurge/jquery-asGradient/master/dist/jquery-asGradient.min.js) - minified

#### Install From Bower
```sh
bower install jquery-asGradient --save
```

#### Install From Npm
```sh
npm install jquery-asGradient --save
```

#### Install From Yarn
```sh
yarn add jquery-asGradient
```

#### Build From Source
If you want build from source:

```sh
git clone git@github.com:amazingSurge/jquery-asGradient.git
cd jquery-asGradient
npm install
npm install -g gulp-cli babel-cli
gulp build
```

Done!

## Requirements
`jquery-asGradient` requires the latest version of [`jQuery`](https://jquery.com/download/) and [`jQuery-asColor`](https://github.com/amazingSurge/jquery-asColor).

## Usage
#### Including files:

```html
<script src="/path/to/jquery.js"></script>
<script src="/path/to/jquery-asColor.js"></script>
<script src="/path/to/jquery-asGradient.js"></script>
```

#### Initialization
All you need to do is call the plugin on the element:

```javascript
var gradient = new AsGradient('linear-gradient(to rgba(0, 0, 0, 1), rgba(255, 255, 255, 1))', {
  cleanPosition: true,
  color: {
    format: 'rgba'
  }
});
```

## Examples
There are some example usages that you can look at to get started. They can be found in the
[examples folder](https://github.com/amazingSurge/jquery-asGradient/tree/master/examples).

## Options
`jquery-asGradient` can accept an options object to alter the way it behaves. You can see the default options by call `$.asGradient.setDefaults()`. The structure of an options object is as follows:

```
{
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
}
```

## Methods

```javascript
var gradient = new AsGradient('linear-gradient(to bottom, yellow, blue)');

gradient.toString();
```

#### toString()
Get gradient string.
```javascript
// Get standard string.
gradient.toString();

// Get string by prefix.
gradient.toString('-moz-');
```

#### fromString()
Set values from gradient string.
```javascript
gradient.fromString('linear-gradient(to bottom, yellow 0%, blue 100%)');
```

#### getPrefixedStrings()
Get prefixed strings array.
```javascript
gradient.getPrefixedStrings();
```

#### val()
Get or set gradient string.
```javascript
// get gradient string
gradient.val();

// set gradient string
gradient.val('linear-gradient(to bottom, yellow 0%, blue 100%)');
```

#### angle()
Get or set angle.
```javascript
// get gradient angle
gradient.angle();

// set gradient angle
gradient.angle(60);
```

#### append(color, position)
Append a new color stop.
```javascript
gradient.append('#fff', '50%');
```

#### insert(color, position, index)
Insert a color stop to index
```javascript
gradient.append('#fff', '50%', 1);
```

#### getCurrent()
Get current color stop.
```javascript
var stop = gradient.getCurrent();
```

#### setCurrentById(id)
Set current color stop by id.
```javascript
gradient.setCurrentById(2);
```

#### getById(id)
Get color stop by index.
```javascript
var stop = gradient.get(2);
```

#### removeById(id)
Remove color stop by id.
```javascript
gradient.removeById(2);
```

#### get(index)
Get color stop by index.
```javascript
var stop = gradient.get(2);
```

#### remove(index)
Remove color stop by index.
```javascript
gradient.remove(2);
```

#### empty()
Empty color stops.
```javascript
gradient.empty();
```

#### reset()
Reset gradient.
```javascript
gradient.reset();
```

## No conflict
If you have to use other plugin with the same namespace, just call the `$.asGradient.noConflict` method to revert to it.

```html
<script src="other-plugin.js"></script>
<script src="jquery-asGradient.js"></script>
<script>
  $.asGradient.noConflict();
  // Code that uses other plugin's "$().asGradient" can follow here.
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
review the [guidelines for contributing](CONTRIBUTING.md). Make sure you're using the latest version of `jquery-asGradient` before submitting an issue. There are several ways to help out:

* [Bug reports](CONTRIBUTING.md#bug-reports)
* [Feature requests](CONTRIBUTING.md#feature-requests)
* [Pull requests](CONTRIBUTING.md#pull-requests)
* Write test cases for open bug issues
* Contribute to the documentation

## Development
`jquery-asGradient` is built modularly and uses Gulp as a build system to build its distributable files. To install the necessary dependencies for the build system, please run:

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
To see the list of recent changes, see [Releases section](https://github.com/amazingSurge/jquery-asGradient/releases).

## Copyright and license
Copyright (C) 2016 amazingSurge.

Licensed under [the LGPL license](LICENSE).

[⬆ back to top](#table-of-contents)

[bower-image]: https://img.shields.io/bower/v/jquery-asGradient.svg?style=flat
[bower-link]: https://david-dm.org/amazingSurge/jquery-asGradient/dev-status.svg
[npm-image]: https://badge.fury.io/js/jquery-asGradient.svg?style=flat
[npm-url]: https://npmjs.org/package/jquery-asGradient
[license]: https://img.shields.io/npm/l/jquery-asGradient.svg?style=flat
[prs-welcome]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
[daviddm-image]: https://david-dm.org/amazingSurge/jquery-asGradient.svg?style=flat
[daviddm-url]: https://david-dm.org/amazingSurge/jquery-asGradient
