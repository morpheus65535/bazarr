import { useSystemSettings } from "@/apis/hooks";

export const uiPageSizeKey = "settings-general-page_size";

export const usePageSize = () => {
  const settings = useSystemSettings();

  return settings.data?.general.page_size ?? 50;
};
