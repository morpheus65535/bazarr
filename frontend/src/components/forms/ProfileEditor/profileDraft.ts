import { cloneDeep } from "lodash";
import { collectGroupItems } from "@/pages/Settings/Languages/profileModel";

// Local, editable copy of a languages profile. Every profile is edited as a list of requirement groups.
export interface ProfileDraft {
  profileId: number;
  name: string;
  tag: string | undefined;
  cutoff: number | null;
  mustContain: string[];
  mustNotContain: string[];
  originalFormat: boolean;
  groups: Language.EnhancedGroup[];
}

export const toProfileDraft = (profile: Language.Profile): ProfileDraft => ({
  profileId: profile.profileId,
  name: profile.name,
  tag: profile.tag,
  cutoff: profile.cutoff,
  mustContain: cloneDeep(profile.mustContain),
  mustNotContain: cloneDeep(profile.mustNotContain),
  originalFormat: profile.originalFormat ?? false,
  groups: cloneDeep(profile.groups),
});

export const draftToProfile = (draft: ProfileDraft): Language.Profile => ({
  profileId: draft.profileId,
  name: draft.name,
  tag: draft.tag,
  profileType: "enhanced",
  cutoff: draft.cutoff,
  items: collectGroupItems(draft.groups),
  groups: draft.groups,
  mustContain: draft.mustContain,
  mustNotContain: draft.mustNotContain,
  originalFormat: draft.originalFormat,
});
