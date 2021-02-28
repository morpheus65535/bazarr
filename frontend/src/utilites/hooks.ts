import { useEffect, useMemo, useState } from "react";
import { mergeArray } from ".";

export function useOnShow(callback: () => void) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!show) {
      setShow(true);
      callback();
    }
  }, [show]); // eslint-disable-line react-hooks/exhaustive-deps
}

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

const characters = "abcdef0123456789";
const randomGenerator = () => {
  return Array(8)
    .fill(null)
    .map(() => characters.charAt(Math.floor(Math.random() * characters.length)))
    .join("");
};

export function useRandom() {
  const [random] = useState(randomGenerator);
  return random;
}

export function useMergeArray<T extends object>(
  olds: readonly T[],
  news: readonly T[],
  key: keyof T
) {
  return useMemo(() => mergeArray(olds, news, key), [olds, news, key]);
}
