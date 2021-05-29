import { useCallback } from "react";
import { useLocalstorageState } from "rooks";

export const uiPageSizeKey = "storage-ui-pageSize";

export function useUpdateLocalStorage() {
  return useCallback((newVals: LooseObject) => {
    for (const key in newVals) {
      const value = newVals[key];
      localStorage.setItem(key, value);
    }
  }, []);
}

export function usePageSize() {
  return useLocalstorageState(uiPageSizeKey, 50);
}
