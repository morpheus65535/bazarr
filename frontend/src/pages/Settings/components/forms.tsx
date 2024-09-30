import { FunctionComponent, ReactNode } from "react";
import {
  Input,
  NumberInput,
  NumberInputProps,
  PasswordInput,
  PasswordInputProps,
  Slider as MantineSlider,
  SliderProps as MantineSliderProps,
  Switch,
  TextInput,
  TextInputProps,
} from "@mantine/core";
import {
  Action as GlobalAction,
  FileBrowser,
  FileBrowserProps,
  MultiSelector as GlobalMultiSelector,
  MultiSelectorProps as GlobalMultiSelectorProps,
  Selector as GlobalSelector,
  SelectorProps as GlobalSelectorProps,
} from "@/components";
import { ActionProps as GlobalActionProps } from "@/components/inputs/Action";
import ChipInput, { ChipInputProps } from "@/components/inputs/ChipInput";
import { BaseInput, useBaseInput } from "@/pages/Settings/utilities/hooks";
import { useSliderMarks } from "@/utilities";

export type NumberProps = BaseInput<number> & NumberInputProps;

export const Number: FunctionComponent<NumberProps> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <NumberInput
      {...rest}
      value={value ?? 0}
      onChange={(val) => {
        if (val === "") {
          val = 0;
        }

        if (typeof val === "string") {
          return update(+val);
        }

        update(val);
      }}
    ></NumberInput>
  );
};

export type TextProps = BaseInput<string | number> & TextInputProps;

export const Text: FunctionComponent<TextProps> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <TextInput
      {...rest}
      value={value ?? ""}
      onChange={(e) => {
        update(e.currentTarget.value);
      }}
    ></TextInput>
  );
};

export type PasswordProps = BaseInput<string> & PasswordInputProps;

export const Password: FunctionComponent<PasswordProps> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <PasswordInput
      {...rest}
      value={value ?? ""}
      onChange={(e) => {
        update(e.currentTarget.value);
      }}
    ></PasswordInput>
  );
};

export interface CheckProps extends BaseInput<boolean> {
  label?: string;
  inline?: boolean;
}

export const Check: FunctionComponent<CheckProps> = ({ label, ...props }) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <Switch
      label={label}
      onChange={(e) => {
        update(e.currentTarget.checked);
      }}
      disabled={rest.disabled}
      checked={value ?? false}
    ></Switch>
  );
};

export type SelectorProps<T extends string | number> = BaseInput<T> &
  GlobalSelectorProps<T>;

export function Selector<T extends string | number>(props: SelectorProps<T>) {
  const { value, update, rest } = useBaseInput(props);

  return (
    <GlobalSelector {...rest} value={value} onChange={update}></GlobalSelector>
  );
}

export type MultiSelectorProps<T extends string | number> = BaseInput<T[]> &
  GlobalMultiSelectorProps<T>;

export function MultiSelector<T extends string | number>(
  props: MultiSelectorProps<T>,
) {
  const { value, update, rest } = useBaseInput(props);

  return (
    <GlobalMultiSelector
      {...rest}
      value={value ?? []}
      onChange={update}
    ></GlobalMultiSelector>
  );
}

type SliderProps = BaseInput<number> &
  Omit<MantineSliderProps, "onChange" | "onChangeEnd" | "marks" | "label"> & {
    label?: ReactNode;
  };

export const Slider: FunctionComponent<SliderProps> = (props) => {
  const { value, update, rest } = useBaseInput(props);
  const { label, ...sliderProps } = rest;

  const { min = 0, max = 100 } = props;

  const marks = useSliderMarks([min, max]);

  return (
    <Input.Wrapper label={label}>
      <MantineSlider
        {...sliderProps}
        marks={marks}
        labelAlwaysOn
        onChange={update}
        value={value ?? 0}
      ></MantineSlider>
    </Input.Wrapper>
  );
};

type ChipsProp = BaseInput<string[]> &
  Omit<ChipInputProps, "onChange" | "data"> & {
    sanitizeFn?: (values: string[] | null) => string[] | undefined;
  };

export const Chips: FunctionComponent<ChipsProp> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  const handleChange = (value: string[] | null) => {
    const sanitizedValues = props.sanitizeFn?.(value) ?? value;

    update(sanitizedValues || null);
  };

  return (
    <ChipInput
      {...rest}
      value={value ?? []}
      onChange={handleChange}
    ></ChipInput>
  );
};

type ActionProps = {
  onClick?: (update: (v: string) => void, value?: string) => void;
} & Omit<BaseInput<string>, "modification">;

export const Action: FunctionComponent<
  Override<ActionProps, GlobalActionProps>
> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <GlobalAction
      {...rest}
      onClick={() => {
        props.onClick?.(update, (value as string) ?? undefined);
      }}
    ></GlobalAction>
  );
};

interface FileProps extends BaseInput<string> {}

export const File: FunctionComponent<Override<FileProps, FileBrowserProps>> = (
  props,
) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <FileBrowser
      {...rest}
      defaultValue={value ?? undefined}
      onChange={update}
    ></FileBrowser>
  );
};
