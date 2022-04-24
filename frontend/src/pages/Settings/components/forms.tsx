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
import { FunctionComponent, ReactText, useEffect } from "react";
import { useCollapse, useSettingValue } from ".";
import { useFormActions } from "../utilities/FormValues";
import { OverrideFuncType } from "./hooks";

export interface BaseInput<T> {
  disabled?: boolean;
  settingKey: string;
  override?: OverrideFuncType<T>;
  beforeStaged?: (v: T) => unknown;
}

export type NumberProps = BaseInput<number> & NumberInputProps;

export const Number: FunctionComponent<NumberProps> = ({
  beforeStaged,
  override,
  settingKey,
  ...props
}) => {
  const value = useSettingValue<number>(settingKey, override);
  const { setValue } = useFormActions();

  return (
    <NumberInput
      {...props}
      value={value ?? undefined}
      onChange={(val = 0) => {
        const value = beforeStaged ? beforeStaged(val) : val;
        setValue(value, settingKey);
      }}
    ></NumberInput>
  );
};

export type TextProps = BaseInput<ReactText> & TextInputProps;

export const Text: FunctionComponent<TextProps> = ({
  beforeStaged,
  override,
  settingKey,
  ...props
}) => {
  const value = useSettingValue<ReactText>(settingKey, override);
  const { setValue } = useFormActions();

  const collapse = useCollapse();

  return (
    <TextInput
      {...props}
      value={value ?? undefined}
      onChange={(e) => {
        const val = e.currentTarget.value;
        collapse && collapse(val.toString());
        const value = beforeStaged ? beforeStaged(val) : val;
        setValue(value, settingKey);
      }}
    ></TextInput>
  );
};

export type PasswordProps = BaseInput<string> & PasswordInputProps;

export const Password: FunctionComponent<PasswordProps> = ({
  settingKey,
  override,
  beforeStaged,
  ...props
}) => {
  const value = useSettingValue<ReactText>(settingKey, override);
  const { setValue } = useFormActions();

  return (
    <PasswordInput
      {...props}
      value={value ?? undefined}
      onChange={(e) => {
        const val = e.currentTarget.value;
        const value = beforeStaged ? beforeStaged(val) : val;
        setValue(value, settingKey);
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
  override,
  disabled,
  settingKey,
}) => {
  const collapse = useCollapse();
  const value = useSettingValue<boolean>(settingKey, override);
  const { setValue } = useFormActions();

  useEffect(() => collapse && collapse(value ?? false), [collapse, value]);

  return (
    <Switch
      id={settingKey}
      label={label}
      onChange={(e) => {
        const { checked } = e.currentTarget;
        setValue(checked, settingKey);
      }}
      disabled={disabled}
      checked={value ?? false}
    ></Switch>
  );
};

export type SelectorProps<T extends string | number> = BaseInput<T> &
  GlobalSelectorProps<T>;

export function Selector<T extends string | number>(props: SelectorProps<T>) {
  const { settingKey, override, beforeStaged, ...selector } = props;

  const value = useSettingValue<T>(settingKey, override);
  const { setValue } = useFormActions();

  return (
    <GlobalSelector
      {...selector}
      value={value}
      onChange={(v) => {
        const result = beforeStaged && v ? beforeStaged(v) : v;
        setValue(result, settingKey);
      }}
    ></GlobalSelector>
  );
}

export type MultiSelectorProps<T extends string | number> = BaseInput<T[]> &
  GlobalMultiSelectorProps<T>;

export function MultiSelector<T extends string | number>(
  props: MultiSelectorProps<T>
) {
  const { settingKey, override, beforeStaged, ...selector } = props;

  const value = useSettingValue<T[]>(settingKey, override);
  const { setValue } = useFormActions();

  return (
    <GlobalMultiSelector
      {...selector}
      value={value ?? []}
      onChange={(v) => {
        const result = beforeStaged && v ? beforeStaged(v) : v;
        setValue(result, settingKey);
      }}
    ></GlobalMultiSelector>
  );
}

type SliderProps = BaseInput<number> &
  Omit<MantineSliderProps, "onChange" | "onChangeEnd" | "marks">;

export const Slider: FunctionComponent<SliderProps> = (props) => {
  const { settingKey, override, ...slider } = props;

  const value = useSettingValue<number>(settingKey, override);
  const { setValue } = useFormActions();

  const marks = useSliderMarks([(slider.min = 0), (slider.max = 100)]);

  return (
    <MantineSlider
      marks={marks}
      onChange={(v) => {
        setValue(v, settingKey);
      }}
      value={value ?? 0}
      {...slider}
    ></MantineSlider>
  );
};

type ChipsProp = BaseInput<string[]> &
  Omit<ChipInputProps, "onChange" | "data">;

export const Chips: FunctionComponent<ChipsProp> = (props) => {
  const { settingKey, override, ...chips } = props;

  const value = useSettingValue<string[]>(settingKey, override);
  const { setValue } = useFormActions();

  return (
    <ChipInput
      value={value ?? []}
      onChange={(v) => {
        setValue(v, settingKey);
      }}
      {...chips}
    ></ChipInput>
  );
};

type ActionProps = {
  onClick?: (
    update: (v: unknown, key: string) => void,
    key: string,
    value?: string
  ) => void;
} & Omit<BaseInput<string>, "override" | "beforeStaged">;

export const Action: FunctionComponent<
  Override<ActionProps, GlobalActionProps>
> = (props) => {
  const { onClick, settingKey, ...button } = props;

  const value = useSettingValue<string>(settingKey);
  const { setValue } = useFormActions();

  return (
    <GlobalAction
      onClick={() => {
        onClick?.(setValue, settingKey, value ?? undefined);
      }}
      {...button}
    ></GlobalAction>
  );
};

interface FileProps extends BaseInput<string> {}

export const File: FunctionComponent<Override<FileProps, FileBrowserProps>> = (
  props
) => {
  const { settingKey, override, ...file } = props;
  const value = useSettingValue<string>(settingKey);
  const { setValue } = useFormActions();

  return (
    <FileBrowser
      defaultValue={value ?? undefined}
      onChange={(p) => {
        setValue(p, settingKey);
      }}
      {...file}
    ></FileBrowser>
  );
};
