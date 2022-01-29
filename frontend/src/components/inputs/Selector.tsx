import clsx from "clsx";
import { FocusEvent, useCallback, useMemo, useRef } from "react";
import Select, { GroupBase, OnChangeValue } from "react-select";
import { SelectComponents } from "react-select/dist/declarations/src/components";

export type SelectorOption<T> = {
  label: string;
  value: T;
};

export type SelectorValueType<T, M extends boolean> = M extends true
  ? ReadonlyArray<T>
  : Nullable<T>;

export interface SelectorProps<T, M extends boolean> {
  className?: string;
  placeholder?: string;
  options: readonly SelectorOption<T>[];
  disabled?: boolean;
  clearable?: boolean;
  loading?: boolean;
  multiple?: M;
  onChange?: (k: SelectorValueType<T, M>) => void;
  onFocus?: (e: FocusEvent<HTMLElement>) => void;
  label?: (item: T) => string;
  defaultValue?: SelectorValueType<T, M>;
  value?: SelectorValueType<T, M>;
  components?: Partial<
    SelectComponents<SelectorOption<T>, M, GroupBase<SelectorOption<T>>>
  >;
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
    onFocus,
    defaultValue,
    components,
    value,
  } = props;

  const labelRef = useRef(label);

  const getName = useCallback(
    (item: T) => {
      if (labelRef.current) {
        return labelRef.current(item);
      }

      return options.find((v) => v.value === item)?.label ?? "Unknown";
    },
    [options]
  );

  const wrapper = useCallback(
    (
      value: SelectorValueType<T, M> | undefined | null
    ):
      | SelectorOption<T>
      | ReadonlyArray<SelectorOption<T>>
      | null
      | undefined => {
      if (value === null || value === undefined) {
        return value as null | undefined;
      } else {
        if (multiple === true) {
          return (value as SelectorValueType<T, true>).map((v) => ({
            label: getName(v),
            value: v,
          }));
        } else {
          const v = value as T;
          return {
            label: getName(v),
            value: v,
          };
        }
      }
    },
    [multiple, getName]
  );

  const defaultWrapper = useMemo(
    () => wrapper(defaultValue),
    [defaultValue, wrapper]
  );

  const valueWrapper = useMemo(() => wrapper(value), [wrapper, value]);

  return (
    <Select
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
      components={components}
      className={clsx("custom-selector w-100", className)}
      classNamePrefix="selector"
      onFocus={onFocus}
      onChange={(newValue) => {
        if (onChange) {
          if (multiple === true) {
            const values = (
              newValue as OnChangeValue<SelectorOption<T>, true>
            ).map((v) => v.value) as ReadonlyArray<T>;

            onChange(values as SelectorValueType<T, M>);
          } else {
            const value = (newValue as OnChangeValue<SelectorOption<T>, false>)
              ?.value;

            onChange(value as SelectorValueType<T, M>);
          }
        }
      }}
    ></Select>
  );
}
