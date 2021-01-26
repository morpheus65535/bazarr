import React, { FunctionComponent, useEffect } from "react";
import { Form } from "react-bootstrap";

import {
  Slider as CSlider,
  SliderProps as CSliderProps,
  Selector as CSelector,
  SingleSelectorProps as CSingleSelectorProps,
  MultiSelectorProps as CMultiSelectorProps,
} from "../../components";

import { useUpdate, useExtract, useCollapse } from ".";

import { isBoolean, isNumber, isString, isArray } from "lodash";

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
  override?: (v: SystemSettings) => T;
  preprocess?: (v: T) => T;
}

export interface TextProps extends BasicInput<React.ReactText> {
  placeholder?: React.ReactText;
  password?: boolean;
}

export const Text: FunctionComponent<TextProps> = ({
  placeholder,
  disabled,
  preprocess,
  override,
  password,
  settingKey,
}) => {
  const defaultValue = useExtract<React.ReactText>(
    settingKey,
    (v): v is React.ReactText => isString(v) || isNumber(v),
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
        const value = preprocess ? preprocess(val) : val;
        collapse(value.toString());
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

  const defaultValue = useExtract<boolean>(settingKey, isBoolean, override);

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

type RemoveSelector<T> = Omit<T, "onSelect" | "onMultiSelect" | "defaultKey">;

type SingleSelectorProps = BasicInput<string> &
  RemoveSelector<CSingleSelectorProps>;

type MultiSelectorProps = BasicInput<string[]> &
  RemoveSelector<CMultiSelectorProps>;

type SelectorProps = SingleSelectorProps | MultiSelectorProps;

export const Selector: FunctionComponent<SelectorProps> = (props) => {
  const update = useUpdate();
  const collapse = useCollapse();

  const { settingKey, override, preprocess, ...selector } = props;

  let defaultValue = useExtract<string | string[]>(
    settingKey,
    (v): v is string | string[] => isString(v) || isNumber(v) || isArray(v),
    override
  );

  if (isNumber(defaultValue)) {
    defaultValue = defaultValue.toString();
  }

  useEffect(() => {
    if (typeof defaultValue === "string") {
      collapse(defaultValue);
    }
  }, [defaultValue, collapse]);

  return (
    <CSelector
      // TODO: Force as any, fix later
      defaultKey={defaultValue as any}
      onSelect={(v) => {
        collapse(v);
        // TODO: Force as any, fix later
        v = preprocess ? (preprocess(v as any) as string) : v;
        update(v, settingKey);
      }}
      onMultiSelect={(v) => {
        // TODO: Force as any, fix later
        v = preprocess ? (preprocess(v as any) as string[]) : v;
        update(v, settingKey);
      }}
      {...selector}
    ></CSelector>
  );
};

type SliderProps = {} & BasicInput<number> &
  Omit<CSliderProps, "onChange" | "onAfterChange">;

export const Slider: FunctionComponent<SliderProps> = (props) => {
  const { settingKey, override, ...slider } = props;

  const update = useUpdate();

  const defaultValue = useExtract<number>(settingKey, isNumber, override);

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
