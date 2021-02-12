import { isArray, isBoolean, isNumber, isString } from "lodash";
import React, { FunctionComponent } from "react";
import {
  Button as BSButton,
  ButtonProps as BSButtonProps,
  Form,
} from "react-bootstrap";
import { UpdateFunctionType, useCollapse, useLatest, useUpdate } from ".";
import {
  Chips as CChips,
  ChipsProps as CChipsProps,
  Selector as CSelector,
  SelectorProps as CSelectorProps,
  Slider as CSlider,
  SliderProps as CSliderProps,
} from "../../components";
import { isReactText, useOnShow } from "../../utilites";
import { OverrideFuncType } from "./hooks";

export const Message: FunctionComponent<{
  type?: "warning" | "info";
}> = ({ type, children }) => {
  const cls = ["pr-4"];
  cls.push(type === "warning" ? "text-warning" : "text-muted");

  return <Form.Text className={cls.join(" ")}>{children}</Form.Text>;
};

export interface BasicInput<T> {
  disabled?: boolean;
  settingKey: string;
  override?: OverrideFuncType<T>;
  beforeStaged?: (v: T) => any;
}

export interface TextProps extends BasicInput<React.ReactText> {
  placeholder?: React.ReactText;
  password?: boolean;
  controlled?: boolean;
}

export const Text: FunctionComponent<TextProps> = ({
  placeholder,
  disabled,
  beforeStaged,
  controlled,
  override,
  password,
  settingKey,
}) => {
  const value = useLatest<React.ReactText>(settingKey, isReactText, override);

  const update = useUpdate();
  const collapse = useCollapse();

  return (
    <Form.Control
      type={password ? "password" : "text"}
      placeholder={placeholder?.toString()}
      disabled={disabled}
      defaultValue={controlled ? undefined : value}
      value={controlled ? value : undefined}
      onChange={(e) => {
        const val = e.currentTarget.value;
        collapse(val.toString());
        const value = beforeStaged ? beforeStaged(val) : val;
        update(value, settingKey);
      }}
    ></Form.Control>
  );
};

export interface CheckProps extends BasicInput<boolean> {
  label?: string;
  inline?: boolean;
}

export const Check: FunctionComponent<CheckProps> = ({
  label,
  inline,
  override,
  disabled,
  settingKey,
}) => {
  const update = useUpdate();
  const collapse = useCollapse();

  const defaultValue = useLatest<boolean>(settingKey, isBoolean, override);

  useOnShow(() => {
    collapse(defaultValue ?? false);
  });

  return (
    <Form.Check
      custom
      type="checkbox"
      id={settingKey}
      inline={inline}
      label={label}
      onChange={(e) => {
        const { checked } = e.currentTarget;
        collapse(checked);
        update(checked, settingKey);
      }}
      disabled={disabled}
      defaultChecked={defaultValue}
    ></Form.Check>
  );
};

function selectorValidator<T>(v: any): v is T {
  return isString(v) || isNumber(v) || isArray(v);
}

type SelectorProps<T, M extends boolean> = BasicInput<SelectorValueType<T, M>> &
  CSelectorProps<T, M>;

export function Selector<
  T extends string | string[] | number | number[],
  M extends boolean = false
>(props: SelectorProps<T, M>) {
  const update = useUpdate();
  const collapse = useCollapse();

  const { settingKey, override, beforeStaged, ...selector } = props;

  const defaultValue = useLatest<SelectorValueType<T, M>>(
    settingKey,
    selectorValidator,
    override
  );

  useOnShow(() => {
    if (typeof defaultValue === "string") {
      collapse(defaultValue);
    }
  });

  return (
    <CSelector
      {...selector}
      // TODO: Force as any
      defaultValue={defaultValue as any}
      onChange={(v) => {
        if (v === undefined) {
          collapse("");
        } else if (typeof v === "string") {
          collapse(v);
        }
        v = beforeStaged ? beforeStaged(v) : v;
        update(v, settingKey);
      }}
    ></CSelector>
  );
}

type SliderProps = {} & BasicInput<number> &
  Omit<CSliderProps, "onChange" | "onAfterChange">;

export const Slider: FunctionComponent<SliderProps> = (props) => {
  const { settingKey, override, ...slider } = props;

  const update = useUpdate();

  const defaultValue = useLatest<number>(settingKey, isNumber, override);

  return (
    <CSlider
      onAfterChange={(v) => {
        update(v, settingKey);
      }}
      defaultValue={defaultValue}
      {...slider}
    ></CSlider>
  );
};

type ChipsProp = {} & BasicInput<string[]> &
  Omit<CChipsProps, "onChange" | "defaultValue">;

export const Chips: FunctionComponent<ChipsProp> = (props) => {
  const { settingKey, override, ...chips } = props;

  const update = useUpdate();

  const defaultValue = useLatest<string[]>(settingKey, isArray, override);

  return (
    <CChips
      defaultValue={defaultValue}
      onChange={(v) => {
        update(v, settingKey);
      }}
      {...chips}
    ></CChips>
  );
};

type ButtonProps = {
  onClick?: (update: UpdateFunctionType, key: string, value?: string) => void;
} & Omit<BasicInput<string>, "override" | "beforeStaged">;

export const Button: FunctionComponent<Override<ButtonProps, BSButtonProps>> = (
  props
) => {
  const { onClick, settingKey, ...button } = props;

  const value = useLatest<string>(settingKey, isString);
  const update = useUpdate();

  return (
    <BSButton
      onClick={() => {
        onClick && onClick(update, settingKey, value);
      }}
      {...button}
    ></BSButton>
  );
};
