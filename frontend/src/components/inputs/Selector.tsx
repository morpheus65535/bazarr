import { useCallback, useMemo } from "react";
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

const DefaultKeyBuilder = <T,>(value: T) => {
  if (typeof value === "string") {
    return value;
  } else if (typeof value === "number" || typeof value === "boolean") {
    return value.toString();
  } else {
    LOG("error", "Unknown value type", value);
    throw new Error(
      `Invalid type (${typeof value}) in the SelectorOption, please provide a label builder`,
    );
  }
};

export interface GroupedSelectorOptions<T> {
  group: string;
  items: SelectorOption<T>[];
}

export type GroupedSelectorProps<T> = Override<
  {
    options: GroupedSelectorOptions<T>[];
    getkey?: (value: T) => string;
  },
  Omit<SelectProps, "data">
>;

export const GroupedSelector = <T,>({
  options,
  ...select
}: GroupedSelectorProps<T>) => (
  <Select
    data-testid="input-selector"
    comboboxProps={{ withinPortal: true }}
    data={options as unknown as ComboboxItemGroup<string>[]}
    {...select}
  ></Select>
);

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

export const Selector = <T,>({
  value,
  defaultValue,
  options,
  onChange,
  getkey = DefaultKeyBuilder,
  ...select
}: SelectorProps<T>) => {
  const data = useMemo(
    () =>
      options.map<SelectItemWithPayload<T>>(({ value, label, ...option }) => ({
        label,
        value: getkey(value),
        payload: value,
        ...option,
      })),
    [getkey, options],
  );

  const wrappedValue = useMemo(() => {
    if (isNull(value) || isUndefined(value)) {
      return value;
    } else {
      return getkey(value);
    }
  }, [getkey, value]);

  const wrappedDefaultValue = useMemo(() => {
    if (isNull(defaultValue) || isUndefined(defaultValue)) {
      return defaultValue;
    } else {
      return getkey(defaultValue);
    }
  }, [defaultValue, getkey]);

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
};

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

export const MultiSelector = <T,>({
  value,
  defaultValue,
  options,
  onChange,
  getkey = DefaultKeyBuilder,
  buildOption,
  hidePickedOptions = true,
  ...select
}: MultiSelectorProps<T>) => {
  const data = useMemo(
    () =>
      options.map<SelectItemWithPayload<T>>(({ value, ...option }) => ({
        value: getkey(value),
        payload: value,
        ...option,
      })),
    [options, getkey],
  );

  const wrappedValue = useMemo(
    () => value && value.map(getkey),
    [value, getkey],
  );

  const wrappedDefaultValue = useMemo(
    () => defaultValue && defaultValue.map(getkey),
    [defaultValue, getkey],
  );

  const wrappedOnChange = useCallback(
    (values: string[]) => {
      const payloads: T[] = [];
      for (const value of values) {
        const payload = data.find((v) => v.value === value)?.payload;
        if (payload) {
          payloads.push(payload);
        } else if (buildOption) {
          payloads.push(buildOption(value));
        }
      }
      onChange?.(payloads);
    },
    [data, onChange, buildOption],
  );

  return (
    <MultiSelect
      {...select}
      hidePickedOptions={hidePickedOptions}
      value={wrappedValue}
      defaultValue={wrappedDefaultValue}
      onChange={wrappedOnChange}
      data={data}
    ></MultiSelect>
  );
};
