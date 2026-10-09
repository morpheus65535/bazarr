import { useCallback, useMemo } from "react";
import { get, isEqual, isNull, isUndefined, uniqBy } from "lodash";
import {
  HookType,
  useFormActions,
  useStagedValues,
} from "@/pages/Settings/utilities/FormValues";
import { useSettings } from "@/pages/Settings/utilities/useSettings";
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

export const useBaseInput = <T, V>(props: T & BaseInput<V>) => {
  const { settingKey, settingOptions, ...rest } = props;
  // TODO: Opti options
  const value = useSettingValue<V>(settingKey, settingOptions);
  // The original (server/default) value, ignoring any staged changes. Used to
  // detect when a field has been reverted back to its original state.
  const originalValue = useSettingValue<V>(settingKey, {
    ...settingOptions,
    original: true,
  });

  const { setValue, removeValue } = useFormActions();

  const update = useCallback(
    (newValue: V | null) => {
      const moddedValue =
        (newValue && settingOptions?.onSaved?.(newValue)) ?? newValue;

      // Reverting back to the original value should clear the staged change
      // so it no longer counts as an unsaved change.
      if (isEqual(moddedValue, originalValue)) {
        removeValue(settingKey);
      } else {
        setValue(moddedValue, settingKey, settingOptions?.onSubmit as HookType);
      }
    },
    [settingOptions, setValue, removeValue, settingKey, originalValue],
  );

  return { value, update, rest };
};

export const useSettingValue = <T>(
  key: string,
  options?: SettingValueOptions<T>,
): Readonly<Nullable<T>> => {
  const settings = useSettings();

  const originalValue = useMemo(() => {
    const onLoaded = options?.onLoaded;
    const defaultValue = options?.defaultValue;
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
  }, [key, settings, options]);

  const stagedValue = useStagedValues();

  if (key in stagedValue && options?.original !== true) {
    return stagedValue[key] as T;
  } else {
    return originalValue;
  }
};

export const useUpdateArray = <T>(
  key: string,
  current: Readonly<T[]>,
  compare: keyof T,
) => {
  const { setValue } = useFormActions();
  const stagedValue = useStagedValues();

  const staged: Readonly<T[]> = useMemo(() => {
    if (key in stagedValue) {
      return stagedValue[key] as T[];
    } else {
      return current;
    }
  }, [key, stagedValue, current]);

  return useCallback(
    (v: T, hook?: HookType) => {
      const newArray = uniqBy([v, ...staged], compare);
      setValue(newArray, key, hook);
    },
    [staged, setValue, key, compare],
  );
};
