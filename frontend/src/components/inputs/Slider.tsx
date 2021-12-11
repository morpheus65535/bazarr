import RcSlider from "rc-slider";
import "rc-slider/assets/index.css";
import React, { FunctionComponent, useMemo, useState } from "react";
import "./slider.scss";

type TooltipsOptions = boolean | "Always";

export interface SliderProps {
  tooltips?: TooltipsOptions;
  min?: number;
  max?: number;
  step?: number;
  start?: number;
  defaultValue?: number;
  onAfterChange?: (value: number) => void;
  onChange?: (value: number) => void;
}

export const Slider: FunctionComponent<SliderProps> = ({
  min,
  max,
  step,
  tooltips,
  defaultValue,
  onChange,
  onAfterChange,
}) => {
  max = max ?? 100;
  min = min ?? 0;
  step = step ?? 1;

  const [curr, setValue] = useState(defaultValue);

  return (
    <div className="d-flex flex-row align-items-center py-2">
      <span className="text-muted text-nowrap pe-3">{`${min} / ${curr}`}</span>
      <RcSlider
        min={min}
        max={max}
        className="custom-rc-slider"
        step={step}
        defaultValue={defaultValue}
        onChange={(v) => {
          setValue(v);
          onChange && onChange(v);
        }}
        onAfterChange={onAfterChange}
        handle={(props) => (
          <div
            className="rc-slider-handle"
            style={{
              left: `${props.offset}%`,
            }}
          >
            <SliderTooltips
              tooltips={tooltips}
              value={props.value}
            ></SliderTooltips>
          </div>
        )}
      ></RcSlider>
      <span className="text-muted ps-3">{max}</span>
    </div>
  );
};

const SliderTooltips: FunctionComponent<{
  tooltips?: TooltipsOptions;
  value: number;
}> = ({ tooltips, value }) => {
  const cls = useMemo(() => {
    const tipsCls = ["rc-slider-handle-tips"];
    if (tooltips !== undefined) {
      if (typeof tooltips === "string") {
        tipsCls.push("rc-slider-handle-tips-always");
      } else if (tooltips === false) {
        tipsCls.push("rc-slider-handle-tips-hidden");
      }
    }
    return tipsCls.join(" ");
  }, [tooltips]);

  return <span className={cls}>{value}</span>;
};
