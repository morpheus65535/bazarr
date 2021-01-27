import React, { FunctionComponent, useEffect } from "react";
import { Form } from "react-bootstrap";
import {
  Slider as CSlider,
  SliderProps as CSliderProps,
  Selector as CSelector,
  SelectorProps as CSelectorProps,
} from "../../components";
import { useUpdate, useLatest, useCollapse } from ".";
import { isBoolean, isNumber, isString, isArray } from "lodash";
import { isReactText } from "../../utilites";

export const Message: FunctionComponent<{
  type: "warning" | "info";
}> = ({ type, children }) => {
  const cls = ["pr-4"];
  cls.push(type === "warning" ? "text-warning" : "text-muted");

  return <Form.Text className={cls.join(" ")}>{children}</Form.Text>;
};

export interface BasicInput<T> {
  disabled?: boolean;
  settingKey: string;
  override?: (v: SystemSettings) => NonNullable<T>;
  beforeStaged?: (v: T) => any;
}

export interface TextProps extends BasicInput<React.ReactText> {
  placeholder?: React.ReactText;
  password?: boolean;
}

export const Text: FunctionComponent<TextProps> = ({
  placeholder,
  disabled,
  beforeStaged,
  override,
  password,
  settingKey,
}) => {
  const defaultValue = useLatest<React.ReactText>(
    settingKey,
    isReactText,
    override
  );

  const update = useUpdate();
  const collapse = useCollapse();

  return (
    <Form.Control
      type={password ? "password" : "text"}
      placeholder={placeholder?.toString()}
      disabled={disabled}
      defaultValue={defaultValue}
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

  useEffect(() => {
    collapse(defaultValue ?? false);
  }, [defaultValue, collapse]);

  return (
    <Form.Check
      type="checkbox"
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

type SelectorProps<T, M extends boolean> = BasicInput<SelectorValueType<T, M>> &
  CSelectorProps<T, M>;

export function Selector<
  T extends string | string[] | number | number[],
  M extends boolean = false
>(props: SelectorProps<T, M>) {
  const update = useUpdate();
  const collapse = useCollapse();

  const { settingKey, override, beforeStaged, ...selector } = props;

  const defaultValue = useLatest<T>(
    settingKey,
    (v): v is T => isString(v) || isNumber(v) || isArray(v)
  );

  useEffect(() => {
    if (typeof defaultValue === "string") {
      collapse(defaultValue);
    }
  }, [defaultValue, collapse]);

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
