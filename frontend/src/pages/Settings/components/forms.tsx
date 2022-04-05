import {
  FileBrowser,
  FileBrowserProps,
  Selector as GlobalSelector,
  SelectorProps as GlobalSelectorProps,
  Slider as GlobalSlider,
  SliderProps as GlobalSliderProps,
} from "@/components";
import { isReactText } from "@/utilities";
import {
  Button as MantineButton,
  ButtonProps as MantineButtonProps,
  MultiSelect,
  MultiSelectProps,
  Switch,
  Text as MantineText,
  TextInput,
} from "@mantine/core";
import { isArray, isBoolean, isNull, isNumber, isString } from "lodash";
import { FunctionComponent, ReactText, useEffect } from "react";
import { useCollapse, useLatest } from ".";
import { OverrideFuncType, useSingleUpdate } from "./hooks";

export const Message: FunctionComponent<{
  type?: "warning" | "info";
}> = ({ type, children }) => {
  return (
    <MantineText size="sm" color="dimmed">
      {children}
    </MantineText>
  );
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
    <TextInput
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
    ></TextInput>
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
  const update = useSingleUpdate();
  const collapse = useCollapse();

  const value = useLatest<boolean>(settingKey, isBoolean, override);

  useEffect(() => collapse && collapse(value ?? false), [collapse, value]);

  return (
    <Switch
      id={settingKey}
      label={label}
      onChange={(e) => {
        const { checked } = e.currentTarget;
        update(checked, settingKey);
      }}
      disabled={disabled}
      checked={value ?? undefined}
    ></Switch>
  );
};

function selectorValidator<T>(v: unknown): v is T {
  return isString(v) || isNumber(v);
}

type SelectorProps<T> = BaseInput<T> & GlobalSelectorProps<T>;

export function Selector<T extends string | number>(props: SelectorProps<T>) {
  const update = useSingleUpdate();
  const collapse = useCollapse();

  const { settingKey, override, beforeStaged, ...selector } = props;

  const value = useLatest<T>(settingKey, selectorValidator, override);

  useEffect(() => {
    if (isString(value) || isNull(value)) {
      collapse && collapse(value ?? "");
    }
  }, [collapse, value]);

  return (
    <GlobalSelector
      {...selector}
      value={value}
      onChange={(v) => {
        const result = beforeStaged && v ? beforeStaged(v) : v;
        update(result, settingKey);
      }}
    ></GlobalSelector>
  );
}

type SliderProps = BaseInput<number> &
  Omit<GlobalSliderProps, "onChange" | "onAfterChange">;

export const Slider: FunctionComponent<SliderProps> = (props) => {
  const { settingKey, override, ...slider } = props;

  const update = useSingleUpdate();

  const defaultValue = useLatest<number>(settingKey, isNumber, override);

  return (
    <GlobalSlider
      onAfterChange={(v) => {
        update(v, settingKey);
      }}
      defaultValue={defaultValue ?? undefined}
      {...slider}
    ></GlobalSlider>
  );
};

type ChipsProp = BaseInput<string[]> &
  Omit<MultiSelectProps, "onChange" | "data">;

export const Chips: FunctionComponent<ChipsProp> = (props) => {
  const { settingKey, override, ...chips } = props;

  const update = useSingleUpdate();

  const value = useLatest<string[]>(settingKey, isArray, override);

  return (
    <MultiSelect
      data={[...(value ?? [])]}
      onChange={(v) => {
        update(v, settingKey);
      }}
      creatable
      onCreate={(v) => {
        update([...(value ?? []), v], settingKey);
      }}
      {...chips}
    ></MultiSelect>
  );
};

type ButtonProps = {
  onClick?: (
    update: (v: unknown, key: string) => void,
    key: string,
    value?: string
  ) => void;
} & Omit<BaseInput<string>, "override" | "beforeStaged">;

export const Button: FunctionComponent<
  Override<ButtonProps, MantineButtonProps<"button">>
> = (props) => {
  const { onClick, settingKey, ...button } = props;

  const value = useLatest<string>(settingKey, isString);
  const update = useSingleUpdate();

  return (
    <MantineButton
      onClick={() => {
        onClick && onClick(update, settingKey, value ?? undefined);
      }}
      {...button}
    ></MantineButton>
  );
};

interface FileProps extends BaseInput<string> {}

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
