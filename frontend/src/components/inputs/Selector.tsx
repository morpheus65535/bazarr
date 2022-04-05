import { LOG } from "@/utilities/console";
import {
  MultiSelect,
  MultiSelectProps,
  Select,
  SelectItem,
  SelectProps,
} from "@mantine/core";
import { isNull, isUndefined } from "lodash";
import { useCallback, useMemo, useRef } from "react";

export type SelectorOption<T> = Override<
  {
    value: T;
    label: string;
  },
  SelectItem
>;

type SelectItemWithPayload<T> = SelectItem & {
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
      `Invalid type (${typeof value}) in the SelectorOption, please provide a label builder`
    );
  }
}

export type SelectorProps<T> = Override<
  {
    value?: T | null;
    defaultValue?: T | null;
    options: SelectorOption<T>[];
    onChange?: (value: T | null) => void;
    getKey?: (value: T) => string;
  },
  Omit<SelectProps, "data">
>;

export function Selector<T>({
  value,
  defaultValue,
  options,
  onChange,
  getKey = DefaultKeyBuilder,
  ...select
}: SelectorProps<T>) {
  const keyRef = useRef(getKey);

  const data = useMemo(
    () =>
      options.map<SelectItemWithPayload<T>>(({ value, label, ...option }) => ({
        label,
        value: keyRef.current(value),
        payload: value,
        ...option,
      })),
    [options]
  );

  const wrappedValue = useMemo(() => {
    if (isNull(value) || isUndefined(value)) {
      return value;
    } else {
      return keyRef.current(value);
    }
  }, [value]);

  const wrappedDefaultValue = useMemo(() => {
    if (isNull(defaultValue) || isUndefined(defaultValue)) {
      return defaultValue;
    } else {
      return keyRef.current(defaultValue);
    }
  }, [defaultValue]);

  const wrappedOnChange = useCallback(
    (value: string) => {
      const payload = data.find((v) => v.value === value)?.payload ?? null;
      onChange?.(payload);
    },
    [data, onChange]
  );

  return (
    <Select
      data={data}
      defaultValue={wrappedDefaultValue}
      value={wrappedValue}
      onChange={wrappedOnChange}
      {...select}
    ></Select>
  );
}

type MultiSelectorProps<T> = Override<
  {
    value?: readonly T[];
    defaultValue?: readonly T[];
    options: readonly SelectorOption<T>[];
    onChange?: (value: T[]) => void;
    getLabel?: (value: T) => string;
  },
  Omit<MultiSelectProps, "data">
>;

export function MultiSelector<T>({
  value,
  defaultValue,
  options,
  onChange,
  getLabel = DefaultKeyBuilder,
  ...select
}: MultiSelectorProps<T>) {
  const labelRef = useRef(getLabel);

  const data = useMemo(
    () =>
      options.map<SelectItemWithPayload<T>>(({ value, ...option }) => ({
        value: labelRef.current(value),
        payload: value,
        ...option,
      })),
    [options]
  );

  const wrappedValue = useMemo(
    () => value && value.map(labelRef.current),
    [value]
  );
  const wrappedDefaultValue = useMemo(
    () => defaultValue && defaultValue.map(labelRef.current),
    [defaultValue]
  );

  const wrappedOnChange = useCallback(
    (values: string[]) => {
      const payloads: T[] = [];
      for (const value of values) {
        const payload = data.find((v) => v.value === value)?.payload;
        if (payload) {
          payloads.push(payload);
        }
      }
      onChange?.(payloads);
    },
    [data, onChange]
  );

  return (
    <MultiSelect
      value={wrappedValue}
      defaultValue={wrappedDefaultValue}
      onChange={wrappedOnChange}
      {...select}
      data={data}
    ></MultiSelect>
  );
}
