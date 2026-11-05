import { cloneDeep } from "lodash";
import { collectGroupItems } from "@/pages/Settings/Languages/profileModel";

// Local, editable copy of a languages profile. Basic and legacy profiles are
// represented as a single group so the editor can share one code path.
export interface ProfileDraft {
  profileId: number;
  name: string;
  tag: string | undefined;
  profileType: Language.ProfileType | undefined;
  cutoff: number | null;
  mustContain: string[];
  mustNotContain: string[];
  originalFormat: boolean;
  groups: Language.EnhancedGroup[];
}

export const toProfileDraft = (profile: Language.Profile): ProfileDraft => {
  const groups: Language.EnhancedGroup[] =
    profile.profileType === "enhanced" && profile.groups
      ? cloneDeep(profile.groups)
      : [{ id: 1, operator: "AND", items: cloneDeep(profile.items) }];

  return {
    profileId: profile.profileId,
    name: profile.name,
    tag: profile.tag,
    profileType: profile.profileType,
    cutoff: profile.cutoff,
    mustContain: cloneDeep(profile.mustContain),
    mustNotContain: cloneDeep(profile.mustNotContain),
    originalFormat: profile.originalFormat ?? false,
    groups,
  };
};

export const draftToProfile = (draft: ProfileDraft): Language.Profile => {
  const sharedFields = {
    profileId: draft.profileId,
    name: draft.name,
    tag: draft.tag,
    cutoff: draft.cutoff,
    mustContain: draft.mustContain,
    mustNotContain: draft.mustNotContain,
    originalFormat: draft.originalFormat,
  };

  if (draft.profileType === "enhanced") {
    return {
      ...sharedFields,
      profileType: "enhanced",
      items: collectGroupItems(draft.groups),
      groups: draft.groups,
    };
  }

  if (draft.profileType === "basic") {
    return {
      ...sharedFields,
      profileType: "basic",
      items: draft.groups[0]?.items ?? [],
    };
  }

  return { ...sharedFields, items: draft.groups[0]?.items ?? [] };
};
