import { isArray } from "lodash";
import React, { useCallback, useMemo } from "react";
import ReactSelect from "react-select";
import "./selector.scss";

export interface SelectorProps<T, M extends boolean> {
  className?: string;
  placeholder?: string;
  options: readonly SelectorOption<T>[];
  disabled?: boolean;
  clearable?: boolean;
  loading?: boolean;
  multiple?: M;
  onChange?: (k: SelectorValueType<T, M>) => void;
  label?: (item: T) => string;
  defaultValue?: SelectorValueType<T, M>;
  value?: SelectorValueType<T, M>;
}

export function Selector<T = string, M extends boolean = false>(
  props: SelectorProps<T, M>
) {
  const {
    className,
    placeholder,
    label,
    disabled,
    clearable,
    loading,
    options,
    multiple,
    onChange,
    defaultValue,
    value,
  } = props;

  const nameFromItems = useCallback(
    (item: T) => {
      return options.find((v) => v.value === item)?.label;
    },
    [options]
  );

  // TODO: Force as any
  const wrapper = useCallback(
    (value: SelectorValueType<T, M> | undefined | null): any => {
      if (value !== null && value !== undefined) {
        if (multiple) {
          return (value as SelectorValueType<T, true>).map((v) => ({
            label: label ? label(v) : nameFromItems(v) ?? "Unknown",
            value: v,
          }));
        } else {
          const v = value as T;
          return {
            label: label ? label(v) : nameFromItems(v) ?? "Unknown",
            value: v,
          };
        }
      }

      return value;
    },
    [label, multiple, nameFromItems]
  );

  const defaultWrapper = useMemo(() => wrapper(defaultValue), [
    defaultValue,
    wrapper,
  ]);

  const valueWrapper = useMemo(() => wrapper(value), [wrapper, value]);

  return (
    <ReactSelect
      isLoading={loading}
      placeholder={placeholder}
      isSearchable={options.length >= 10}
      isMulti={multiple}
      closeMenuOnSelect={!multiple}
      defaultValue={defaultWrapper}
      value={valueWrapper}
      isClearable={clearable}
      isDisabled={disabled}
      options={options}
      className={`custom-selector w-100 ${className ?? ""}`}
      classNamePrefix="selector"
      onChange={(v) => {
        if (onChange) {
          let res: T | T[] | null = null;
          if (isArray(v)) {
            res = (v as ReadonlyArray<SelectorOption<T>>).map(
              (val) => val.value
            );
          } else {
            res = (v as SelectorOption<T>)?.value ?? null;
          }
          // TODO: Force as any
          onChange(res as any);
        }
      }}
    ></ReactSelect>
  );
}
