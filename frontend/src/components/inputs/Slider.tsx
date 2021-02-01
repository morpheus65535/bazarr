import RcSlider from "rc-slider";
import "rc-slider/assets/index.css";
import React, { FunctionComponent, useMemo } from "react";

type TooltipsOptions = boolean | "Always";

export interface SliderProps {
  tooltips?: TooltipsOptions;
  min?: number;
  max?: number;
  start?: number;
  defaultValue?: number;
  onAfterChange?: (value: number) => void;
  onChange?: (value: number) => void;
}

export const Slider: FunctionComponent<SliderProps> = ({
  min,
  max,
  tooltips,
  defaultValue,
  onChange,
  onAfterChange,
}) => {
  return (
    <div className="d-flex flex-row align-items-center py-2">
      <span className="text-muted pr-3">{min ?? 0}</span>
      <RcSlider
        min={min ?? 0}
        max={max ?? 100}
        className="custom-rc-slider"
        step={1}
        defaultValue={defaultValue}
        onChange={onChange}
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
      <span className="text-muted pl-3">{max ?? 100}</span>
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
