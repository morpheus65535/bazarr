import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useSelector } from "react-redux";
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

export function useLanguageProfiles() {
  return useSelector<StoreState, LanguagesProfile[]>(
    (s) => s.system.languagesProfiles.items
  );
}

export function useProfileBy(id?: number) {
  const profiles = useLanguageProfiles();
  return useMemo(() => profiles.find((v) => v.profileId === id), [
    id,
    profiles,
  ]);
}

export function useLanguages(enabled: boolean = false) {
  return useSelector<StoreState, Language[]>((s) =>
    enabled ? s.system.enabledLanguage.items : s.system.languages.items
  );
}

export function useGetLanguage(enabled: boolean = false) {
  const languages = useLanguages(enabled);
  return useCallback(
    (code?: string) => {
      if (code === undefined) {
        return undefined;
      } else {
        return languages.find((v) => v.code2 === code);
      }
    },
    [languages]
  );
}

export function useLanguageBy(code: string) {
  const getter = useGetLanguage();
  return useMemo(() => getter(code), [code, getter]);
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
