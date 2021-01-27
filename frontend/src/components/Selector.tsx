import React, { useCallback, useMemo } from "react";
import { isArray } from "lodash";
import ReactSelect from "react-select";

export interface SelectorProps<T, M extends boolean> {
  className?: string;
  options: SelectorOption<T>[];
  disabled?: boolean;
  clearable?: boolean;
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
    label,
    disabled,
    clearable,
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
    (value: SelectorValueType<T, M> | undefined): any => {
      if (value) {
        if (multiple) {
          return (value as SelectorValueType<T, true>).map((v) => ({
            label: label ? label(v) : nameFromItems(v) ?? "Unknown",
            value: v,
          }));
        } else {
          const v = value as SelectorValueType<T, false>;
          if (v) {
            return {
              label: label ? label(v) : nameFromItems(v) ?? "Unknown",
              value: v,
            };
          }
        }
      } else {
        return undefined;
      }
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
      isSearchable={options.length >= 10}
      isMulti={multiple}
      closeMenuOnSelect={!multiple}
      defaultValue={defaultWrapper}
      value={valueWrapper}
      isClearable={clearable}
      isDisabled={disabled}
      options={options}
      className={`custom-selector ${className ?? ""}`}
      classNamePrefix="selector"
      onChange={(v) => {
        if (onChange) {
          let res: T | T[] | undefined = undefined;
          if (isArray(v)) {
            res = (v as ReadonlyArray<SelectorOption<T>>).map(
              (val) => val.value
            );
          } else {
            res = (v as SelectorOption<T>)?.value;
          }
          // TODO: Force as any
          onChange(res as any);
        }
      }}
    ></ReactSelect>
  );
}
