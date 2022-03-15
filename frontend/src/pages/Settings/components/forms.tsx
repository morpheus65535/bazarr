import {
  Chips as CChips,
  ChipsProps as CChipsProps,
  FileBrowser,
  FileBrowserProps,
  Selector as CSelector,
  SelectorProps as CSelectorProps,
  SelectorValueType,
  Slider as CSlider,
  SliderProps as CSliderProps,
} from "@/components";
import { isReactText } from "@/utilities";
import { isArray, isBoolean, isNull, isNumber, isString } from "lodash";
import { FunctionComponent, ReactText, useEffect } from "react";
import {
  Button as BSButton,
  ButtonProps as BSButtonProps,
  Form,
} from "react-bootstrap";
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
  beforeStaged?: (v: T) => unknown;
}

export interface TextProps extends BaseInput<ReactText> {
  placeholder?: ReactText;
  password?: boolean;
  controlled?: boolean;
  numberWithArrows?: boolean;
}

export const Text: FunctionComponent<TextProps> = ({
  placeholder,
  disabled,
  beforeStaged,
  controlled,
  override,
  password,
  settingKey,
  numberWithArrows,
}) => {
  const value = useLatest<ReactText>(settingKey, isReactText, override);

  const update = useSingleUpdate();
  const collapse = useCollapse();

  const fieldType = () => {
    if (password) {
      return "password";
    } else if (numberWithArrows) {
      return "number";
    } else {
      return "text";
    }
  };

  return (
    <Form.Control
      type={fieldType()}
      placeholder={placeholder?.toString()}
      disabled={disabled}
      defaultValue={controlled ? undefined : value ?? undefined}
      value={controlled ? value ?? undefined : undefined}
      onChange={(e) => {
        const val = e.currentTarget.value;
        collapse && collapse(val.toString());
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

  useEffect(() => collapse && collapse(value ?? false), [collapse, value]);

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

function selectorValidator<T>(v: unknown): v is T {
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
      collapse && collapse(value ?? "");
    }
  });

  return (
    <CSelector
      {...selector}
      value={value as SelectorValueType<T, M>}
      onChange={(v) => {
        const result = beforeStaged ? beforeStaged(v) : v;
        update(result, settingKey);
      }}
    ></CSelector>
  );
}

type SliderProps = BaseInput<number> &
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

type ChipsProp = BaseInput<string[]> &
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
    update: (v: unknown, key: string) => void,
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

type FileProps = {} & BaseInput<string>;

export const File: FunctionComponent<Override<FileProps, FileBrowserProps>> = (
  props
) => {
  const { settingKey, override, ...file } = props;
  const value = useLatest<string>(settingKey, isString);
  const update = useSingleUpdate();

  return (
    <FileBrowser
      defaultValue={value ?? undefined}
      onChange={(p) => {
        update(p, settingKey);
      }}
      {...file}
    ></FileBrowser>
  );
};
