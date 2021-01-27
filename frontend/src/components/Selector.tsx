import React, { useCallback, useMemo } from "react";
import { isArray } from "lodash";
import ReactSelect from "react-select";

export interface SelectorProps<T, M extends boolean> {
  options: SelectorOption<T>[];
  disabled?: boolean;
  clearable?: boolean;
  multiple?: M;
  onChange?: (k: SelectorValueType<T, M>) => void;
  label?: (item: T) => string;
  defaultValue?: SelectorValueType<T, M>;
}

export function Selector<T = string, M extends boolean = false>(
  props: SelectorProps<T, M>
) {
  const {
    label,
    disabled,
    clearable,
    options,
    multiple,
    onChange,
    defaultValue,
  } = props;

  const nameFromItems = useCallback(
    (item: T) => {
      return options.find((v) => v.value === item)?.label;
    },
    [options]
  );

  const value = useMemo(() => {
    if (defaultValue) {
      if (multiple) {
        return (defaultValue as SelectorValueType<T, true>).map((v) => ({
          label: label ? label(v) : nameFromItems(v) ?? "Unknown",
          value: v,
        }));
      } else {
        const v = defaultValue as SelectorValueType<T, false>;
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
  }, [defaultValue, label, multiple, nameFromItems]);

  return (
    <ReactSelect
      isMulti={multiple}
      closeMenuOnSelect={!multiple}
      // TODO: Force as any
      defaultValue={value as any}
      isClearable={clearable}
      isDisabled={disabled}
      options={options}
      className="custom-selector"
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
