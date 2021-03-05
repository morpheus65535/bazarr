import React, { useCallback, useEffect, useMemo, useState } from "react";
import { mergeArray } from ".";

export function useBaseUrl(slash: boolean = false) {
  if (process.env.NODE_ENV === "development") {
    return "/";
  } else {
    let url = window.Bazarr.baseUrl ?? "/";
    if (slash && !url.endsWith("/")) {
      url += "/";
    }
    return url;
  }
}

export function useCanUpdateInject() {
  if (process.env.NODE_ENV === "development") {
    return process.env["REACT_APP_CAN_UPDATE"] === "true";
  } else {
    return window.Bazarr.canUpdate;
  }
}

export function useHasUpdateInject() {
  if (process.env.NODE_ENV === "development") {
    return process.env["REACT_APP_HAS_UPDATE"] === "true";
  } else {
    return window.Bazarr.hasUpdate;
  }
}

export function useSessionStorage(
  key: string
): [StorageType, React.Dispatch<StorageType>] {
  const dispatch: React.Dispatch<StorageType> = useCallback(
    (value) => {
      if (value !== null) {
        sessionStorage.setItem(key, value);
      } else {
        sessionStorage.removeItem(key);
      }
    },
    [key]
  );
  return [sessionStorage.getItem(key), dispatch];
}

export function useMergeArray<T>(
  olds: readonly T[],
  news: readonly T[],
  comparer: Comparer<T>
) {
  return useMemo(() => mergeArray(olds, news, comparer), [
    olds,
    news,
    comparer,
  ]);
}

export function useAutoUpdate(action: () => void, interval?: number) {
  const [, setHandle] = useState<NodeJS.Timeout | undefined>(undefined);

  const updateHandle = useCallback(
    (enable: boolean, action?: () => void) => {
      if (interval === undefined) {
        return;
      }

      if (enable && action) {
        setHandle(setInterval(action, interval));
      } else if (!enable) {
        setHandle((hd) => {
          if (hd !== undefined) {
            clearInterval(hd);
          }
          return undefined;
        });
      }
    },
    [interval]
  );

  const update = useCallback(() => {
    if (document.visibilityState === "visible") {
      action();
      updateHandle(true, action);
    } else if (document.visibilityState === "hidden") {
      updateHandle(false);
    }
  }, [action, updateHandle]);

  useEffect(() => {
    document.addEventListener("visibilitychange", update);
    update();

    return () => {
      document.removeEventListener("visibilitychange", update);
      updateHandle(false);
    };
  }, [update, updateHandle]);
}
