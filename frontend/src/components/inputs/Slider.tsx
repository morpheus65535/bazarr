import {
  Slider as MantineSlider,
  SliderProps as MantineSliderProps,
} from "@mantine/core";
import { FunctionComponent, useMemo } from "react";

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
  min = 0,
  max = 100,
  step = 1,
  tooltips,
  defaultValue,
  onChange,
  onAfterChange,
}) => {
  const marks = useMemo<MantineSliderProps["marks"]>(
    () => [
      {
        value: min,
        label: min,
      },
      { value: max, label: max },
    ],
    [max, min]
  );

  return (
    <MantineSlider
      marks={marks}
      min={min}
      max={max}
      step={step}
      defaultValue={defaultValue}
      onChange={onChange}
      onChangeEnd={onAfterChange}
    ></MantineSlider>
  );
};
