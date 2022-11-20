import { useLocalStorage } from "@mantine/hooks";
import { useCallback } from "react";

export const uiPageSizeKey = "storage-ui-pageSize";

export function useUpdateLocalStorage() {
  return useCallback((newVals: LooseObject) => {
    for (const key in newVals) {
      const value = newVals[key];
      localStorage.setItem(key, value);
    }
  }, []);
}

export function getPageSize(storage: Storage): number {
  const defaultValue = 50;

  const value = storage.getItem(uiPageSizeKey);

  if (value === null) {
    return defaultValue;
  }

  return JSON.parse(value);
}

export function usePageSize() {
  return useLocalStorage({ key: uiPageSizeKey, defaultValue: 50 });
}
