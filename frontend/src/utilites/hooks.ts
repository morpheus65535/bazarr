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
  comparer: Comparer<NonNullable<T>>
) {
  return useMemo(() => mergeArray(olds, news, comparer), [
    olds,
    news,
    comparer,
  ]);
}

export function useAutoUpdate(action: () => void, interval?: number) {
  const [, setHandle] = useState<NodeJS.Timeout | undefined>(undefined);

  const removeTimer = useCallback(() => {
    setHandle((hd) => {
      if (hd !== undefined) {
        clearInterval(hd);
      }
      return undefined;
    });
  }, [setHandle]);

  const createTimer = useCallback(
    (action?: () => void) => {
      setHandle((hd) => {
        if (hd !== undefined) {
          clearInterval(hd);
        }
        if (action && interval !== undefined) {
          return setInterval(action, interval);
        } else {
          return undefined;
        }
      });
    },
    [interval]
  );

  const update = useCallback(() => {
    if (document.visibilityState === "visible") {
      action();
      createTimer(action);
    } else if (document.visibilityState === "hidden") {
      removeTimer();
    }
  }, [action, createTimer, removeTimer]);

  useEffect(() => {
    document.addEventListener("visibilitychange", update);
    update();

    return () => {
      document.removeEventListener("visibilitychange", update);
      removeTimer();
    };
  }, [update, removeTimer]);
}
