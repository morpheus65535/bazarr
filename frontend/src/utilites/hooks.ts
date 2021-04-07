import React, { useCallback, useEffect, useState } from "react";
import { useHistory } from "react-router";

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

export function useGotoHomepage() {
  const history = useHistory();
  return useCallback(() => history.push("/"), [history]);
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

export function useWatcher<T>(
  curr: T,
  expected: T,
  onSame?: () => void,
  onDiff?: () => void
) {
  const [, setPrevious] = useState(curr);

  useEffect(() => {
    setPrevious((prev) => {
      if (prev !== curr) {
        if (curr !== expected) {
          onDiff && onDiff();
        } else {
          onSame && onSame();
        }
      }
      return curr;
    });
  }, [curr, expected, onDiff, onSame]);
}

export function useWhenLoadingFinish(
  state: Readonly<AsyncState<any>>,
  callback: () => void
) {
  return useWatcher(state.updating, true, undefined, callback);
}
