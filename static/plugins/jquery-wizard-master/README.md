# [jQuery wizard](https://github.com/amazingSurge/jquery-wizard) ![bower][bower-image] [![NPM version][npm-image]][npm-url] [![Dependency Status][daviddm-image]][daviddm-url] [![prs-welcome]](#contributing)

> A jquery plugin for creating step-by-step wizards.

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
├── jquery-wizard.js
├── jquery-wizard.es.js
├── jquery-wizard.min.js
└── css/
    ├── wizard.css
    └── wizard.min.css
```

## Quick start
Several quick start options are available:
#### Download the latest build

 * [Development](https://raw.githubusercontent.com/amazingSurge/jquery-wizard/master/dist/jquery-wizard.js) - unminified
 * [Production](https://raw.githubusercontent.com/amazingSurge/jquery-wizard/master/dist/jquery-wizard.min.js) - minified

#### Install From Bower
```sh
bower install jquery-wizard.js --save
```

#### Install From Npm
```sh
npm install jquery-wizard --save
```

#### Install From Yarn
```sh
yarn add jquery-wizard
```

#### Build From Source
If you want build from source:

```sh
git clone git@github.com:amazingSurge/jquery-wizard.git
cd jquery-wizard
npm install
npm install -g gulp-cli babel-cli
gulp build
```

Done!

## Requirements
`jquery-wizard` requires the latest version of [`jQuery`](https://jquery.com/download/).

## Usage
#### Including files:

```html
<link rel="stylesheet" href="/path/to/wizard.css">
<script src="/path/to/jquery.js"></script>
<script src="/path/to/jquery-wizard.js"></script>
```

#### Required HTML structure

```html
<div class="wizard">
  <ul class="wizard-steps" role="tablist">
    <li class="active" role="tab">
      Step 1
    </li>
    <li role="tab">
      Step 2
    </li>
    <li role="tab">
      Step 3
    </li>
  </ul>
  <div class="wizard-content">
    <div class="wizard-pane active" role="tabpanel">Step Content 1</div>
    <div class="wizard-pane" role="tabpanel">Step Content 2</div>
    <div class="wizard-pane" role="tabpanel">Step Content 3</div>
  </div>
</div>
```

#### Initialization
All you need to do is call the plugin on the element:

```javascript
jQuery(function($) {
  $('.example').wizard(); 
});
```

## Examples
There are some example usages that you can look at to get started. They can be found in the
[examples folder](https://github.com/amazingSurge/jquery-wizard/tree/master/examples).

## Options
`jquery-wizard` can accept an options object to alter the way it behaves. You can see the default options by call `$.wizard.setDefaults()`. The structure of an options object is as follows:

```
{
  step: '.wizard-steps > li',

  getPane: function(index, step) {
    return this.$element.find('.wizard-content').children().eq(index);
  },

  buttonsAppendTo: 'this',
  templates: {
    buttons: function() {
      const options = this.options;
      return `<div class="wizard-buttons"><a class="wizard-back" href="#${this.id}" data-wizard="back" role="button">${options.buttonLabels.back}</a><a class="wizard-next" href="#${this.id}" data-wizard="next" role="button">${options.buttonLabels.next}</a><a class="wizard-finish" href="#${this.id}" data-wizard="finish" role="button">${options.buttonLabels.finish}</a></div>`;
    }
  },

  classes: {
    step: {
      done: 'done',
      error: 'error',
      active: 'current',
      disabled: 'disabled',
      activing: 'activing',
      loading: 'loading'
    },

    pane: {
      active: 'active',
      activing: 'activing'
    },

    button: {
      hide: 'hide',
      disabled: 'disabled'
    }
  },

  autoFocus: true,
  keyboard: true,

  enableWhenVisited: false,

  buttonLabels: {
    next: 'Next',
    back: 'Back',
    finish: 'Finish'
  },

  loading: {
    show: function(step) { },
    hide: function(step) { },
    fail: function(step) { }
  },

  cacheContent: false,

  validator: function(step) {
    return true;
  },

  onInit: null,
  onNext: null,
  onBack: null,
  onReset: null,

  onBeforeShow: null,
  onAfterShow: null,
  onBeforeHide: null,
  onAfterHide: null,
  onBeforeLoad: null,
  onAfterLoad: null,

  onBeforeChange: null,
  onAfterChange: null,

  onStateChange: null,

  onFinish: null
}
```


## Methods
Methods are called on wizard instances through the wizard method itself.
You can also save the instances to variable for further use.

```javascript
// call directly
$().wizard('goTo', 0);

// or
var api = $().data('wizard');
api.goTo(0);
```

#### goTo(index)
Go to the specifc step.
```javascript
// go to the first step
$().wizard('goTo', 0);

// move to 50%
$().wizard('moveTo', '50%');
```

#### length()
Get the steps length.
```javascript
$().wizard('length');
```

#### get(index)
Get the step instance further use.
```javascript
// get the second step instance
var step = $().wizard('get', 1);
```

#### current()
Get the current shown step instance
```javascript
var step = $().wizard('current');
```

#### currentIndex()
Get the current shown step index
```javascript
var index = $().wizard('currentIndex');
```

#### lastIndex()
Get the last index
```javascript
var index = $().wizard('lastIndex');
```

#### next()
Go to the next step
```javascript
$().wizard('next');
```

#### back()
Go back to the previous step
```javascript
$().wizard('back');
```

#### first()
Go back to the first step
```javascript
$().wizard('first');
```

#### finish()
Finish the wizard when the current step is the last one
```javascript
$().wizard('finish');
```

#### reset()
Reset the wizard.
```javascript
$().wizard('reset');
```

#### destroy()
Destroy the wizard instance.
```javascript
$().wizard('destroy');
```

## Events
`jquery-wizard` provides custom events for the plugin’s unique actions. 

```javascript
$('.the-element').on('wizard::ready', function (e) {
  // on instance ready
});

```

Event       | Description
----------- | -----------
init        | Fires when the instance is setup for the first time.
ready       | Fires when the instance is ready for API use.
next        | Fired when the `next` instance method has been called.
back        | Fired when the `back` instance method has been called.
reset       | Fired when the `reset` instance method has been called.
beforeChange| This event is fired before the step change.
afterChange | This event is fired after the step change.
finish      | Fires when the wizard is finished.
destroy     | Fires when an instance is destroyed. 

## No conflict
If you have to use other plugin with the same namespace, just call the `$.wizard.noConflict` method to revert to it.

```html
<script src="other-plugin.js"></script>
<script src="jquery-wizard.js"></script>
<script>
  $.wizard.noConflict();
  // Code that uses other plugin's "$().wizard" can follow here.
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
review the [guidelines for contributing](CONTRIBUTING.md). Make sure you're using the latest version of `jquery-wizard` before submitting an issue. There are several ways to help out:

* [Bug reports](CONTRIBUTING.md#bug-reports)
* [Feature requests](CONTRIBUTING.md#feature-requests)
* [Pull requests](CONTRIBUTING.md#pull-requests)
* Write test cases for open bug issues
* Contribute to the documentation

## Development
`jquery-wizard` is built modularly and uses Gulp as a build system to build its distributable files. To install the necessary dependencies for the build system, please run:

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
To see the list of recent changes, see [Releases section](https://github.com/amazingSurge/jquery-wizard/releases).

## Copyright and license
Copyright (C) 2016 amazingSurge.

Licensed under [the LGPL license](LICENSE).

[⬆ back to top](#table-of-contents)

[bower-image]: https://img.shields.io/bower/v/jquery-wizard.js.svg?style=flat
[bower-link]: https://david-dm.org/amazingSurge/jquery-wizard/dev-status.svg
[npm-image]: https://badge.fury.io/js/jquery-wizard.svg?style=flat
[npm-url]: https://npmjs.org/package/jquery-wizard
[license]: https://img.shields.io/npm/l/jquery-wizard.svg?style=flat
[prs-welcome]: https://img.shields.io/badge/PRs-welcome-brightgreen.svg
[daviddm-image]: https://david-dm.org/amazingSurge/jquery-wizard.svg?style=flat
[daviddm-url]: https://david-dm.org/amazingSurge/jquery-wizard