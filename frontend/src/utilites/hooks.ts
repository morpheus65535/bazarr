import React, { useCallback, useEffect, useMemo } from "react";
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
  const update = useCallback(() => {
    if (document.visibilityState === "visible") {
      action();
    }
  }, [action]);

  useEffect(() => {
    document.addEventListener("visibilitychange", update);
    update();

    let handle: NodeJS.Timeout | undefined = undefined;

    if (interval !== undefined) {
      handle = setInterval(update, interval);
    }

    return () => {
      document.removeEventListener("visibilitychange", update);
      if (handle !== undefined) {
        clearInterval(handle);
      }
    };
  }, [update, action, interval]);
}
