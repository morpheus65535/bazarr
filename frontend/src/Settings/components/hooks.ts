import { useMemo } from "react";
import { useSettings, useStaged } from "./provider";

export function useExtract<T>(
  key: string,
  validate: (v: any) => v is T,
  override?: (settings: SystemSettings) => T
) {
  const settings = useSettings();

  const extractValue = useMemo(() => {
    let value: T | undefined = undefined;

    if (override) {
      return override(settings);
    }

    const path = key.split("-");

    if (path[0] !== "settings") {
      return undefined;
    }

    let item: LooseObject = settings;
    for (const key of path) {
      if (key !== "settings" && key in item) {
        item = item[key];
      }

      if (validate(item)) {
        value = item;
        break;
      }
    }

    return value;
  }, [key, settings, validate, override]);

  return extractValue;
}

export function useLatest<T>(key: string, validate: (v: any) => v is T) {
  const extractValue = useExtract<T>(key, validate);
  const stagedValue = useStaged();
  if (key in stagedValue) {
    return stagedValue[key] as T;
  } else {
    return extractValue;
  }
}
