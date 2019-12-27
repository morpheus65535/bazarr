import Color from 'jquery-asColor';
import GradientString from './gradientString';

export default class ColorStop {
  constructor(color, position, gradient) {
    this.color = Color(color, gradient.options.color);
    this.position = GradientString.parsePosition(position);
    this.id = ++gradient._stopIdCount;
    this.gradient = gradient;
  }

  setPosition(string) {
    const position = GradientString.parsePosition(string);
    if(this.position !== position){
      this.position = position;
      this.gradient.reorder();
    }
  }

  setColor(string) {
    this.color.fromString(string);
  }

  remove() {
    this.gradient.removeById(this.id);
  }
}
