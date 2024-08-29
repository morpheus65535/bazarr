import { useCallback, useMemo, useRef } from "react";
import {
  ComboboxItem,
  ComboboxItemGroup,
  MultiSelect,
  MultiSelectProps,
  Select,
  SelectProps,
} from "@mantine/core";
import { isNull, isUndefined } from "lodash";
import { LOG } from "@/utilities/console";

export type SelectorOption<T> = Override<
  {
    value: T;
    label: string;
  },
  ComboboxItem
>;

type SelectItemWithPayload<T> = ComboboxItem & {
  payload: T;
};

function DefaultKeyBuilder<T>(value: T) {
  if (typeof value === "string") {
    return value;
  } else if (typeof value === "number") {
    return value.toString();
  } else {
    LOG("error", "Unknown value type", value);
    throw new Error(
      `Invalid type (${typeof value}) in the SelectorOption, please provide a label builder`,
    );
  }
}

export interface GroupedSelectorOptions<T> {
  group: string;
  items: SelectorOption<T>[];
}

export type GroupedSelectorProps<T> = Override<
  {
    options: ComboboxItemGroup[];
    getkey?: (value: T) => string;
  },
  Omit<SelectProps, "data">
>;

export function GroupedSelector<T>({
  options,
  ...select
}: GroupedSelectorProps<T>) {
  return (
    <Select
      data-testid="input-selector"
      comboboxProps={{ withinPortal: true }}
      data={options}
      {...select}
    ></Select>
  );
}

export type SelectorProps<T> = Override<
  {
    value?: T | null;
    defaultValue?: T | null;
    options: SelectorOption<T>[];
    onChange?: (value: T | null) => void;
    getkey?: (value: T) => string;
  },
  Omit<SelectProps, "data">
>;

export function Selector<T>({
  value,
  defaultValue,
  options,
  onChange,
  getkey = DefaultKeyBuilder,
  ...select
}: SelectorProps<T>) {
  const keyRef = useRef(getkey);
  keyRef.current = getkey;

  const data = useMemo(
    () =>
      options.map<SelectItemWithPayload<T>>(({ value, label, ...option }) => ({
        label,
        value: keyRef.current(value),
        payload: value,
        ...option,
      })),
    [keyRef, options],
  );

  const wrappedValue = useMemo(() => {
    if (isNull(value) || isUndefined(value)) {
      return value;
    } else {
      return keyRef.current(value);
    }
  }, [keyRef, value]);

  const wrappedDefaultValue = useMemo(() => {
    if (isNull(defaultValue) || isUndefined(defaultValue)) {
      return defaultValue;
    } else {
      return keyRef.current(defaultValue);
    }
  }, [defaultValue, keyRef]);

  const wrappedOnChange = useCallback(
    (value: string | null) => {
      const payload = data.find((v) => v.value === value)?.payload ?? null;
      onChange?.(payload);
    },
    [data, onChange],
  );

  return (
    <Select
      data-testid="input-selector"
      comboboxProps={{ withinPortal: true }}
      data={data}
      defaultValue={wrappedDefaultValue}
      value={wrappedValue}
      onChange={wrappedOnChange}
      {...select}
    ></Select>
  );
}

export type MultiSelectorProps<T> = Override<
  {
    value?: readonly T[];
    defaultValue?: readonly T[];
    options: readonly SelectorOption<T>[];
    onChange?: (value: T[]) => void;
    getkey?: (value: T) => string;
    buildOption?: (value: string) => T;
  },
  Omit<MultiSelectProps, "data">
>;

export function MultiSelector<T>({
  value,
  defaultValue,
  options,
  onChange,
  getkey = DefaultKeyBuilder,
  buildOption,
  ...select
}: MultiSelectorProps<T>) {
  const labelRef = useRef(getkey);
  labelRef.current = getkey;

  const buildRef = useRef(buildOption);
  buildRef.current = buildOption;

  const data = useMemo(
    () =>
      options.map<SelectItemWithPayload<T>>(({ value, ...option }) => ({
        value: labelRef.current(value),
        payload: value,
        ...option,
      })),
    [options],
  );

  const wrappedValue = useMemo(
    () => value && value.map(labelRef.current),
    [value],
  );

  const wrappedDefaultValue = useMemo(
    () => defaultValue && defaultValue.map(labelRef.current),
    [defaultValue],
  );

  const wrappedOnChange = useCallback(
    (values: string[]) => {
      const payloads: T[] = [];
      for (const value of values) {
        const payload = data.find((v) => v.value === value)?.payload;
        if (payload) {
          payloads.push(payload);
        } else if (buildRef.current) {
          payloads.push(buildRef.current(value));
        }
      }
      onChange?.(payloads);
    },
    [data, onChange],
  );

  return (
    <MultiSelect
      {...select}
      hidePickedOptions
      value={wrappedValue}
      defaultValue={wrappedDefaultValue}
      onChange={wrappedOnChange}
      data={data}
    ></MultiSelect>
  );
}
