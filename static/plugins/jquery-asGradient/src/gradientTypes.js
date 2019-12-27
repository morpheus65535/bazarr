import $ from 'jquery';
import GradientString from './gradientString';

export default {
  LINEAR: {
    parse(result) {
      return {
        r: (result[1].substr(-1) === '%') ? parseInt(result[1].slice(0, -1) * 2.55, 10) : parseInt(result[1], 10),
        g: (result[2].substr(-1) === '%') ? parseInt(result[2].slice(0, -1) * 2.55, 10) : parseInt(result[2], 10),
        b: (result[3].substr(-1) === '%') ? parseInt(result[3].slice(0, -1) * 2.55, 10) : parseInt(result[3], 10),
        a: 1
      };
    },
    to(gradient, instance, prefix) {
      if (gradient.stops.length === 0) {
        return instance.options.emptyString;
      }
      if (gradient.stops.length === 1) {
        return gradient.stops[0].color.to(instance.options.degradationFormat);
      }

      let standard = instance.options.forceStandard;
      let _prefix = instance._prefix;

      if (!_prefix) {
        standard = true;
      }
      if (prefix && -1 !== $.inArray(prefix, instance.options.prefixes)) {
        standard = false;
        _prefix = prefix;
      }

      const angle = GradientString.formatAngle(gradient.angle, !standard, instance.options.angleUseKeyword);
      const stops = GradientString.formatStops(gradient.stops, instance.options.cleanPosition);

      const output = `linear-gradient(${angle}, ${stops})`;
      if (standard) {
        return output;
      } else {
        return _prefix + output;
      }
    }
  }
};
