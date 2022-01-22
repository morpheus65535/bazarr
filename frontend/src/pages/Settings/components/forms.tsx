import {
  Chips as CChips,
  ChipsProps as CChipsProps,
  Selector as CSelector,
  SelectorProps as CSelectorProps,
  Slider as CSlider,
  SliderProps as CSliderProps,
} from "components";
import { isArray, isBoolean, isNull, isNumber, isString } from "lodash";
import React, { FunctionComponent, useEffect } from "react";
import {
  Button as BSButton,
  ButtonProps as BSButtonProps,
  Form,
} from "react-bootstrap";
import { isReactText } from "utilities";
import { useCollapse, useLatest } from ".";
import { OverrideFuncType, useSingleUpdate } from "./hooks";

export const Message: FunctionComponent<{
  type?: "warning" | "info";
}> = ({ type, children }) => {
  const cls = ["pr-4"];
  cls.push(type === "warning" ? "text-warning" : "text-muted");

  return <Form.Text className={cls.join(" ")}>{children}</Form.Text>;
};

export interface BaseInput<T> {
  disabled?: boolean;
  settingKey: string;
  override?: OverrideFuncType<T>;
  beforeStaged?: (v: T) => any;
}

export interface TextProps extends BaseInput<React.ReactText> {
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

  const update = useSingleUpdate();
  const collapse = useCollapse();

  return (
    <Form.Control
      type={password ? "password" : "text"}
      placeholder={placeholder?.toString()}
      disabled={disabled}
      defaultValue={controlled ? undefined : value ?? undefined}
      value={controlled ? value ?? undefined : undefined}
      onChange={(e) => {
        const val = e.currentTarget.value;
        collapse(val.toString());
        const value = beforeStaged ? beforeStaged(val) : val;
        update(value, settingKey);
      }}
    ></Form.Control>
  );
};

export interface CheckProps extends BaseInput<boolean> {
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
  const update = useSingleUpdate();
  const collapse = useCollapse();

  const value = useLatest<boolean>(settingKey, isBoolean, override);

  useEffect(() => collapse(value ?? false), [collapse, value]);

  return (
    <Form.Check
      custom
      type="checkbox"
      id={settingKey}
      inline={inline}
      label={label}
      onChange={(e) => {
        const { checked } = e.currentTarget;
        update(checked, settingKey);
      }}
      disabled={disabled}
      checked={value ?? undefined}
    ></Form.Check>
  );
};

function selectorValidator<T>(v: any): v is T {
  return isString(v) || isNumber(v) || isArray(v);
}

type SelectorProps<T, M extends boolean> = BaseInput<SelectorValueType<T, M>> &
  CSelectorProps<T, M>;

export function Selector<
  T extends string | string[] | number | number[],
  M extends boolean = false
>(props: SelectorProps<T, M>) {
  const update = useSingleUpdate();
  const collapse = useCollapse();

  const { settingKey, override, beforeStaged, ...selector } = props;

  const value = useLatest<SelectorValueType<T, M>>(
    settingKey,
    selectorValidator,
    override
  );

  useEffect(() => {
    if (isString(value) || isNull(value)) {
      collapse(value ?? "");
    }
  });

  return (
    <CSelector
      {...selector}
      // TODO: Force as any
      defaultValue={value as any}
      onChange={(v) => {
        v = beforeStaged ? beforeStaged(v) : v;
        update(v, settingKey);
      }}
    ></CSelector>
  );
}

type SliderProps = {} & BaseInput<number> &
  Omit<CSliderProps, "onChange" | "onAfterChange">;

export const Slider: FunctionComponent<SliderProps> = (props) => {
  const { settingKey, override, ...slider } = props;

  const update = useSingleUpdate();

  const defaultValue = useLatest<number>(settingKey, isNumber, override);

  return (
    <CSlider
      onAfterChange={(v) => {
        update(v, settingKey);
      }}
      defaultValue={defaultValue ?? undefined}
      {...slider}
    ></CSlider>
  );
};

type ChipsProp = {} & BaseInput<string[]> &
  Omit<CChipsProps, "onChange" | "defaultValue">;

export const Chips: FunctionComponent<ChipsProp> = (props) => {
  const { settingKey, override, ...chips } = props;

  const update = useSingleUpdate();

  const value = useLatest<string[]>(settingKey, isArray, override);

  return (
    <CChips
      value={value ?? undefined}
      onChange={(v) => {
        update(v, settingKey);
      }}
      {...chips}
    ></CChips>
  );
};

type ButtonProps = {
  onClick?: (
    update: (v: any, key: string) => void,
    key: string,
    value?: string
  ) => void;
} & Omit<BaseInput<string>, "override" | "beforeStaged">;

export const Button: FunctionComponent<Override<ButtonProps, BSButtonProps>> = (
  props
) => {
  const { onClick, settingKey, ...button } = props;

  const value = useLatest<string>(settingKey, isString);
  const update = useSingleUpdate();

  return (
    <BSButton
      onClick={() => {
        onClick && onClick(update, settingKey, value ?? undefined);
      }}
      {...button}
    ></BSButton>
  );
};
