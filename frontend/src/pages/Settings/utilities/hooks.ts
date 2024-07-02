import { useCallback, useMemo, useRef } from "react";
import { get, isNull, isUndefined, uniqBy } from "lodash";
import {
  HookType,
  useFormActions,
  useStagedValues,
} from "@/pages/Settings/utilities/FormValues";
import { useSettings } from "@/pages/Settings/utilities/SettingsProvider";
import { LOG } from "@/utilities/console";

export interface BaseInput<T> {
  disabled?: boolean;
  settingKey: string;
  settingOptions?: SettingValueOptions<T>;
}

export type SettingValueOptions<T> = {
  original?: boolean;
  defaultValue?: T;
  onLoaded?: (settings: Settings) => T;
  onSaved?: (value: T) => unknown;
  onSubmit?: (value: T) => unknown;
};

export function useBaseInput<T, V>(props: T & BaseInput<V>) {
  const { settingKey, settingOptions, ...rest } = props;
  // TODO: Opti options
  const value = useSettingValue<V>(settingKey, settingOptions);

  const { setValue } = useFormActions();

  const update = useCallback(
    (newValue: V | null) => {
      const moddedValue =
        (newValue && settingOptions?.onSaved?.(newValue)) ?? newValue;

      setValue(moddedValue, settingKey, settingOptions?.onSubmit);
    },
    [settingOptions, setValue, settingKey],
  );

  return { value, update, rest };
}

export function useSettingValue<T>(
  key: string,
  options?: SettingValueOptions<T>,
): Readonly<Nullable<T>> {
  const settings = useSettings();

  const optionsRef = useRef(options);
  optionsRef.current = options;

  const originalValue = useMemo(() => {
    const onLoaded = optionsRef.current?.onLoaded;
    const defaultValue = optionsRef.current?.defaultValue;
    if (onLoaded && settings) {
      LOG("info", `${key} is using custom loader`);

      return onLoaded(settings);
    }

    const path = key.replaceAll("-", ".");

    const value = get({ settings }, path, null) as Nullable<T>;

    if (defaultValue && (isNull(value) || isUndefined(value))) {
      LOG("info", `${key} is falling back to`, defaultValue);

      return defaultValue;
    }

    return value;
  }, [key, settings]);

  const stagedValue = useStagedValues();

  if (key in stagedValue && optionsRef.current?.original !== true) {
    return stagedValue[key] as T;
  } else {
    return originalValue;
  }
}

export function useUpdateArray<T>(
  key: string,
  current: Readonly<T[]>,
  compare: keyof T,
) {
  const { setValue } = useFormActions();
  const stagedValue = useStagedValues();

  const compareRef = useRef(compare);
  compareRef.current = compare;

  const staged: T[] = useMemo(() => {
    if (key in stagedValue) {
      return stagedValue[key];
    } else {
      return current;
    }
  }, [key, stagedValue, current]);

  return useCallback(
    (v: T, hook?: HookType) => {
      const newArray = uniqBy([v, ...staged], compareRef.current);
      setValue(newArray, key, hook);
    },
    [staged, setValue, key],
  );
}
