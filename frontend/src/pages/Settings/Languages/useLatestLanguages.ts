import { useLanguageProfiles } from "@/apis/hooks";
import { enabledLanguageKey, languageProfileKey } from "@/pages/Settings/keys";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import { useEnabledLanguages } from "@/utilities/languages";

export const useLatestEnabledLanguages = () => {
  const { data } = useEnabledLanguages();
  const latest = useSettingValue<Language.Info[]>(enabledLanguageKey);

  if (latest) {
    return latest;
  } else {
    return data;
  }
};

export const useLatestProfiles = () => {
  const { data = [] } = useLanguageProfiles();
  const latest = useSettingValue<Language.Profile[]>(languageProfileKey);

  if (latest) {
    return latest;
  } else {
    return data;
  }
};
