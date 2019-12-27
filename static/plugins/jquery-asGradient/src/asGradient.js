import $ from 'jquery';
import DEFAULTS from './defaults';
import * as util from './util';
import GradientString from './gradientString';
import ColorStop from './colorStop';
import GradientTypes from './gradientTypes';

class AsGradient {
  constructor(string, options) {
    if (typeof string === 'object' && typeof options === 'undefined') {
      options = string;
      string = undefined;
    }
    this.value = {
      angle: 0,
      stops: []
    };
    this.options = $.extend(true, {}, DEFAULTS, options);

    this._type = 'LINEAR';
    this._prefix = null;
    this.length = this.value.stops.length;
    this.current = 0;
    this._stopIdCount = 0;

    this.init(string);
  }

  init(string) {
    if (string) {
      this.fromString(string);
    }
  }

  val(value) {
    if (typeof value === 'undefined') {
      return this.toString();
    } else {
      this.fromString(value);
      return this;
    }
  }

  angle(value) {
    if (typeof value === 'undefined') {
      return this.value.angle;
    } else {
      this.value.angle = GradientString.parseAngle(value);
      return this;
    }
  }

  append(color, position) {
    return this.insert(color, position, this.length);
  }

  reorder() {
    if(this.length < 2){
      return;
    }

    this.value.stops = this.value.stops.sort((a, b) => a.position - b.position);
  }

  insert(color, position, index) {
    if (typeof index === 'undefined') {
      index = this.current;
    }

    const stop = new ColorStop(color, position, this);

    this.value.stops.splice(index, 0, stop);

    this.length = this.length + 1;
    this.current = index;
    return stop;
  }

  getById(id) {
    if(this.length > 0){
      for(const i in this.value.stops){
        if(id === this.value.stops[i].id){
          return this.value.stops[i];
        }
      }
    }
    return false;
  }

  removeById(id) {
    const index = this.getIndexById(id);
    if(index){
      this.remove(index);
    }
  }

  getIndexById(id) {
    let index = 0;
    for(const i in this.value.stops){
      if(id === this.value.stops[i].id){
        return index;
      }
      index ++;
    }
    return false;
  }

  getCurrent() {
    return this.value.stops[this.current];
  }

  setCurrentById(id) {
    let index = 0;
    for(const i in this.value.stops){
      if(this.value.stops[i].id !== id){
        index ++;
      } else {
        this.current = index;
      }
    }
  }

  get(index) {
    if (typeof index === 'undefined') {
      index = this.current;
    }
    if (index >= 0 && index < this.length) {
      this.current = index;
      return this.value.stops[index];
    } else {
      return false;
    }
  }

  remove(index) {
    if (typeof index === 'undefined') {
      index = this.current;
    }
    if (index >= 0 && index < this.length) {
      this.value.stops.splice(index, 1);
      this.length = this.length - 1;
      this.current = index - 1;
    }
  }

  empty() {
    this.value.stops = [];
    this.length = 0;
    this.current = 0;
  }

  reset() {
    this.value._angle = 0;
    this.empty();
    this._prefix = null;
    this._type = 'LINEAR';
  }

  type(type) {
    if (typeof type === 'string' && (type = type.toUpperCase()) && typeof GradientTypes[type] !== 'undefined') {
      this._type = type;
      return this;
    } else {
      return this._type;
    }
  }

  fromString(string) {
    this.reset();

    const result = GradientString.parseString(string);

    if (result) {
      this._prefix = result.prefix;
      this.type(result.type);
      if (result.value) {
        this.value.angle = GradientString.parseAngle(result.value.angle, this._prefix !== null);

        $.each(result.value.stops, (i, stop) => {
          this.append(stop.color, stop.position);
        });
      }
    }
  }

  toString(prefix) {
    if(prefix === true){
      prefix = util.getPrefix();
    }
    return GradientTypes[this.type()].to(this.value, this, prefix);
  }

  matchString(string) {
    return GradientString.matchString(string);
  }

  toStringWithAngle(angle, prefix) {
    const value = $.extend(true, {}, this.value);
    value.angle = GradientString.parseAngle(angle);

    if(prefix === true){
      prefix = util.getPrefix();
    }

    return GradientTypes[this.type()].to(value, this, prefix);
  }

  getPrefixedStrings() {
    const strings = [];
    for (let i in this.options.prefixes) {
      if(Object.hasOwnProperty.call(this.options.prefixes, i)){
        strings.push(this.toString(this.options.prefixes[i]));
      }
    }
    return strings;
  }

  static setDefaults(options) {
    $.extend(true, DEFAULTS, $.isPlainObject(options) && options);
  }
}

export default AsGradient;
