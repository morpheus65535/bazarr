import { ASSERT, LOG } from "@/utilities/console";
import { get, isNull, isUndefined, uniqBy } from "lodash";
import { useCallback, useMemo, useRef } from "react";
import {
  FormKey,
  useFormActions,
  useStagedValues,
} from "../utilities/FormValues";
import { useSettings } from "../utilities/SettingsProvider";
import { useSubmitHookWith } from "./HooksProvider";

export interface BaseInput<T> {
  disabled?: boolean;
  settingKey: string;
  location?: FormKey;
  settingOptions?: SettingValueOptions<T>;
}

export type SettingValueOptions<T> = {
  original?: boolean;
  defaultValue?: T;
  onLoaded?: (settings: Settings, storage: Storage) => T;
  onSaved?: (value: T) => unknown;
  onSubmit?: (value: T) => unknown;
};

export function useBaseInput<T, V>(props: T & BaseInput<V>) {
  const { settingKey, settingOptions, location, ...rest } = props;
  // TODO: Opti options
  const value = useSettingValue<V>(settingKey, settingOptions);

  const { setValue } = useFormActions();

  const update = useCallback(
    (newValue: V | null) => {
      const moddedValue =
        (newValue && settingOptions?.onSaved?.(newValue)) ?? newValue;

      setValue(moddedValue, settingKey, location);
    },
    [settingOptions, setValue, settingKey, location]
  );

  return { value, update, rest };
}

export function useSettingValue<T>(
  key: string,
  options?: SettingValueOptions<T>
): Readonly<Nullable<T>> {
  const settings = useSettings();
  const storage = window.localStorage;

  const isSettingsKey = useMemo(() => key.startsWith("settings"), [key]);

  ASSERT(isSettingsKey === false && key.startsWith("storage"));

  const optionsRef = useRef(options);
  optionsRef.current = options;

  useSubmitHookWith(key, options?.onSubmit);

  const originalValue = useMemo(() => {
    const onLoaded = optionsRef.current?.onLoaded;
    const defaultValue = optionsRef.current?.defaultValue;
    if (onLoaded) {
      LOG("info", `${key} is using custom loader`);

      return onLoaded(settings, storage);
    }

    let value: Nullable<T> = null;
    if (isSettingsKey) {
      const path = key.replaceAll("-", ".");

      value = get({ settings }, path, null) as Nullable<T>;
    } else {
      const storageValue = storage.getItem(key);
      if (storageValue !== null) {
        value = JSON.parse(storageValue);
      }
    }

    if (defaultValue && (isNull(value) || isUndefined(value))) {
      LOG("info", `${key} is falling back to`, defaultValue);

      return defaultValue;
    }

    return value;
  }, [isSettingsKey, key, settings, storage]);

  const stagedValue = useStagedValues();

  if (key in stagedValue && optionsRef.current?.original !== true) {
    return stagedValue[key] as T;
  } else {
    return originalValue;
  }
}

export function useUpdateArray<T>(key: string, compare: keyof T) {
  const { setValue } = useFormActions();
  const stagedValue = useStagedValues();

  const compareRef = useRef(compare);
  compareRef.current = compare;

  const staged: T[] = useMemo(() => {
    if (key in stagedValue) {
      return stagedValue[key];
    } else {
      return [];
    }
  }, [key, stagedValue]);

  return useCallback(
    (v: T) => {
      const newArray = uniqBy([v, ...staged], compareRef.current);
      setValue(newArray, key);
    },
    [staged, setValue, key]
  );
}
