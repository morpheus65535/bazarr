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
import { useSliderMarks } from "@/utilities";
import {
  InputWrapper,
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
import { FunctionComponent, ReactText } from "react";
import { BaseInput, useBaseInput } from "../utilities/hooks";

export type NumberProps = BaseInput<number> & NumberInputProps;

export const Number: FunctionComponent<NumberProps> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <NumberInput
      {...rest}
      value={value ?? undefined}
      onChange={(val = 0) => {
        update(val);
      }}
    ></NumberInput>
  );
};

export type TextProps = BaseInput<ReactText> & TextInputProps;

export const Text: FunctionComponent<TextProps> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <TextInput
      {...rest}
      value={value ?? undefined}
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
      value={value ?? undefined}
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

export const Check: FunctionComponent<CheckProps> = ({
  label,
  inline,
  ...props
}) => {
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
  props: MultiSelectorProps<T>
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
  Omit<MantineSliderProps, "onChange" | "onChangeEnd" | "marks">;

export const Slider: FunctionComponent<SliderProps> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  const { min = 0, max = 100 } = props;

  const marks = useSliderMarks([min, max]);

  return (
    <InputWrapper label={rest.label}>
      <MantineSlider
        {...rest}
        marks={marks}
        onChange={update}
        value={value ?? 0}
      ></MantineSlider>
    </InputWrapper>
  );
};

type ChipsProp = BaseInput<string[]> &
  Omit<ChipInputProps, "onChange" | "data">;

export const Chips: FunctionComponent<ChipsProp> = (props) => {
  const { value, update, rest } = useBaseInput(props);

  return (
    <ChipInput {...rest} value={value ?? []} onChange={update}></ChipInput>
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
  props
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
