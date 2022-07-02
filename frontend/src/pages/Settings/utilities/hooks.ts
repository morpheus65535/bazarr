import { LOG } from "@/utilities/console";
import { get, isNull, isUndefined, uniqBy } from "lodash";
import { useCallback, useEffect, useMemo, useRef } from "react";
import { submitHooks } from "../components";
import {
  FormKey,
  useFormActions,
  useStagedValues,
} from "../utilities/FormValues";
import { useSettings } from "../utilities/SettingsProvider";

export interface BaseInput<T> {
  disabled?: boolean;
  settingKey: string;
  location?: FormKey;
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

  const optionsRef = useRef(options);

  useEffect(() => {
    const onSubmit = optionsRef.current?.onSubmit;
    if (onSubmit) {
      LOG("info", "Adding submit hook for", key);
      submitHooks[key] = onSubmit;
    }

    return () => {
      if (key in submitHooks) {
        LOG("info", "Removing submit hook for", key);
        delete submitHooks[key];
      }
    };
  }, [key]);

  const originalValue = useMemo(() => {
    const onLoaded = optionsRef.current?.onLoaded;
    const defaultValue = optionsRef.current?.defaultValue;
    if (onLoaded) {
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
