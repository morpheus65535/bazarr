import { useCallback, useMemo } from "react";
import { languageProfileKey } from "@/pages/Settings/keys";
import {
  HookType,
  useFormActions,
} from "@/pages/Settings/utilities/FormValues";
import { nextProfileId, removeProfileAt, upsertProfile } from "./profileModel";
import { serializeProfiles } from "./profileSerialization";
import { useLatestProfiles } from "./useLatestLanguages";

// Stages create, update and delete operations on the latest staged profile list.
export const useProfileActions = () => {
  const profiles = useLatestProfiles();
  const { setValue } = useFormActions();

  const submitProfiles = useCallback(
    (list: Language.Profile[]) => {
      setValue(list, languageProfileKey, ((value: Language.Profile[]) =>
        serializeProfiles(value)) as HookType);
    },
    [setValue],
  );

  const updateProfile = useCallback(
    (profile: Language.Profile) =>
      submitProfiles(upsertProfile(profiles, profile)),
    [profiles, submitProfiles],
  );

  const removeProfile = useCallback(
    (index: number) => submitProfiles(removeProfileAt(profiles, index)),
    [profiles, submitProfiles],
  );

  const createProfileId = useMemo(() => nextProfileId(profiles), [profiles]);

  return { profiles, updateProfile, removeProfile, createProfileId };
};
