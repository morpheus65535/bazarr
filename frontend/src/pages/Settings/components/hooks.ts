import { useSystemSettings } from "@/apis/hooks";
import { LOG } from "@/utilities/console";
import { isArray, uniqBy } from "lodash";
import { useCallback, useContext, useMemo } from "react";
import { StagedChangesContext } from "./Layout";

export function useStagedValues(): LooseObject {
  const [values] = useContext(StagedChangesContext);
  return values;
}

export function useSingleUpdate() {
  const [, update] = useContext(StagedChangesContext);
  return useCallback(
    (v: unknown, key: string) => {
      update((staged) => {
        const changes = { ...staged };
        changes[key] = v;

        LOG("info", "stage settings", changes);

        return changes;
      });
    },
    [update]
  );
}

export function useMultiUpdate() {
  const [, update] = useContext(StagedChangesContext);
  return useCallback(
    (obj: LooseObject) => {
      update((staged) => {
        const changes = { ...staged, ...obj };

        LOG("info", "stage settings", changes);

        return changes;
      });
    },
    [update]
  );
}

type ValidateFuncType<T> = (v: unknown) => v is T;

export type OverrideFuncType<T> = (settings: Settings) => T;

export function useExtract<T>(
  key: string,
  validate: ValidateFuncType<T>,
  override?: OverrideFuncType<T>
): Readonly<Nullable<T>> {
  const { data: settings } = useSystemSettings();

  const extractValue = useMemo(() => {
    let value: Nullable<T> = null;

    if (settings === undefined) {
      return value;
    }

    let path = key.split("-");

    if (path[0] !== "settings") {
      return null;
    } else {
      path = path.slice(0);
    }

    let item: LooseObject = settings;
    for (const key of path) {
      if (key in item) {
        item = item[key];
      }

      if (validate(item)) {
        value = item;
        break;
      }
    }

    return value;
  }, [key, settings, validate]);

  if (override && settings !== undefined) {
    // TODO: Temporarily override
    return override(settings);
  } else {
    return extractValue;
  }
}

export function useLatest<T>(
  key: string,
  validate: ValidateFuncType<T>,
  override?: OverrideFuncType<T>
): Readonly<Nullable<T>> {
  const extractValue = useExtract<T>(key, validate, override);
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
  const extractValue = useExtract<T[]>(key, isArray, override);
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
  const update = useSingleUpdate();
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
      update(newArray, key);
    },
    [compare, staged, key, update]
  );
}
