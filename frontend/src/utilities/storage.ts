import { useCallback } from "react";
import { useSystemSettings } from "@/apis/hooks";

export const uiPageSizeKey = "settings-general-page_size";

export function useUpdateLocalStorage() {
  return useCallback((newVals: LooseObject) => {
    for (const key in newVals) {
      const value = newVals[key];
      localStorage.setItem(key, value);
    }
  }, []);
}

export function usePageSize() {
  const settings = useSystemSettings();

  return settings.data?.general.page_size ?? 50;
}
