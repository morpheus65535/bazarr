import { get, uniqBy } from "lodash";
import { useCallback, useMemo, useRef } from "react";
import { useFormActions, useStagedValues } from "../utilities/FormValues";
import { useSettings } from "../utilities/SettingsProvider";

export type OverrideFuncType<T> = (settings: Settings) => T;

export function useExtract<T>(
  key: string,
  override?: OverrideFuncType<T>
): Readonly<Nullable<T>> {
  const settings = useSettings();

  const overrideRef = useRef(override);
  overrideRef.current = override;

  const extractValue = useMemo(() => {
    if (overrideRef.current) {
      return overrideRef.current(settings);
    }

    const path = key.replaceAll("-", ".");

    const value = get({ settings }, path, null) as Nullable<T>;

    return value;
  }, [key, settings]);

  return extractValue;
}

export function useSettingValue<T>(
  key: string,
  override?: OverrideFuncType<T>
): Readonly<Nullable<T>> {
  const extractValue = useExtract<T>(key, override);
  const stagedValue = useStagedValues();
  if (key in stagedValue) {
    return stagedValue[key] as T;
  } else {
    return extractValue;
  }
}

export function useLatestArray<T>(
  key: string,
  compare: keyof T,
  override?: OverrideFuncType<T[]>
): Readonly<Nullable<T[]>> {
  const extractValue = useExtract<T[]>(key, override);
  const stagedValue = useStagedValues();

  let staged: T[] | undefined = undefined;
  if (key in stagedValue) {
    staged = stagedValue[key];
  }

  return useMemo(() => {
    if (staged !== undefined && extractValue) {
      return uniqBy([...staged, ...extractValue], compare);
    } else {
      return extractValue;
    }
  }, [extractValue, staged, compare]);
}

export function useUpdateArray<T>(key: string, compare: keyof T) {
  const { setValue } = useFormActions();
  const stagedValue = useStagedValues();

  const staged: T[] = useMemo(() => {
    if (key in stagedValue) {
      return stagedValue[key];
    } else {
      return [];
    }
  }, [key, stagedValue]);

  return useCallback(
    (v: T) => {
      const newArray = uniqBy([v, ...staged], compare);
      setValue(newArray, key);
    },
    [staged, compare, setValue, key]
  );
}
