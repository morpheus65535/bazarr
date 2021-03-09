import { isArray, isEqual } from "lodash";
import { useCallback, useContext, useMemo } from "react";
import { useStore } from "react-redux";
import { useSystemSettings } from "../../@redux/hooks";
import { mergeArray } from "../../utilites";
import { log } from "../../utilites/logger";
import { StagedChangesContext } from "./provider";

export function useStagedValues(): LooseObject {
  const [values] = useContext(StagedChangesContext);
  return values;
}

export function useSingleUpdate() {
  const [, update] = useContext(StagedChangesContext);
  return useCallback(
    (v: any, key: string) => {
      update((staged) => {
        const changes = { ...staged };
        changes[key] = v;

        log("info", "stage settings", changes);

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

        log("info", "stage settings", changes);

        return changes;
      });
    },
    [update]
  );
}

type ValidateFuncType<T> = (v: any) => v is T;

export type OverrideFuncType<T> = (settings: Settings, store: ReduxStore) => T;

export function useExtract<T>(
  key: string,
  validate: ValidateFuncType<T>,
  override?: OverrideFuncType<T>
): Readonly<Nullable<T>> {
  const [systemSettings] = useSystemSettings();
  const settings = systemSettings.items;

  const store = useStore<ReduxStore>();

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
    return override(settings, store.getState());
  } else {
    return extractValue;
  }
}

export function useUpdateArray<T>(
  key: string,
  compare?: (one: T, another: T) => boolean
) {
  const update = useSingleUpdate();
  const stagedValue = useStagedValues();

  if (compare === undefined) {
    compare = isEqual;
  }

  const staged: T[] = useMemo(() => {
    if (key in stagedValue) {
      return stagedValue[key];
    } else {
      return [];
    }
  }, [key, stagedValue]);

  return useCallback(
    (v: T) => {
      const newArray = [...staged];
      const idx = newArray.findIndex((inn) => compare!(inn, v));
      if (idx !== -1) {
        newArray[idx] = v;
      } else {
        newArray.push(v);
      }
      update(newArray, key);
    },
    [compare, staged, key, update]
  );
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

// Merge Two Array
export function useLatestMergeArray<T>(
  key: string,
  compare: Comparer<T>,
  override?: OverrideFuncType<T[]>
): Readonly<Nullable<T[]>> {
  const extractValue = useExtract<T[]>(key, isArray, override);
  const stagedValue = useStagedValues();

  if (compare === undefined) {
    compare = isEqual;
  }

  let staged: T[] | undefined = undefined;
  if (key in stagedValue) {
    staged = stagedValue[key];
  }

  return useMemo(() => {
    if (staged !== undefined && extractValue) {
      return mergeArray(extractValue, staged, compare);
    } else {
      return extractValue;
    }
  }, [extractValue, staged, compare]);
}
