import { cloneDeep, includes, maxBy } from "lodash";
import { anyCutoff } from "@/components/forms/profileOptions";

// Domain helpers for language profiles: creation, identity and ordering.
// Wire-format concerns live in profileSerialization.ts.

export const createProfileItem = (
  id: number,
  language: string,
): Language.ProfileItem => ({
  id,
  language,
  audioExclude: "False",
  audioOnlyInclude: "False",
  hi: "False",
  forced: "False",
});

export const nextItemId = (items: readonly Language.ProfileItem[]): number =>
  1 + items.reduce((max, item) => Math.max(item.id, max), 0);

export const collectGroupItems = (
  groups: readonly Language.EnhancedGroup[],
): Language.ProfileItem[] => groups.flatMap((group) => group.items);

// Enhanced group ids must stay unique and can never collide with the "any group" cutoff.
export const nextGroupId = (
  groups: readonly Language.EnhancedGroup[],
): number => {
  const candidate =
    1 + groups.reduce((max, group) => Math.max(group.id, max), 0);

  return candidate === anyCutoff ? candidate + 1 : candidate;
};

export const nextProfileId = (profiles: readonly Language.Profile[]): number =>
  1 + profiles.reduce((max, profile) => Math.max(profile.profileId, max), 0);

// A language cannot repeat with the same subtitle type inside one group, matching the backend key.
export const isLanguageRepeated = (
  items: readonly Language.ProfileItem[],
): boolean =>
  new Set(items.map((item) => `${item.language}|${item.hi}|${item.forced}`))
    .size !== items.length;

export const createEnhancedProfile = (
  profileId: number,
  language: string | undefined,
): Language.Profile => {
  const groups: Language.EnhancedGroup[] =
    language === undefined
      ? []
      : [{ id: 1, operator: "AND", items: [createProfileItem(1, language)] }];

  return {
    profileId,
    name: "",
    tag: undefined,
    profileType: "enhanced",
    items: collectGroupItems(groups),
    groups,
    cutoff: null,
    mustContain: [],
    mustNotContain: [],
    originalFormat: false,
  };
};

// Legacy profiles once shipped duplicated item ids; make them unique again on edit.
export const repairDuplicateItemIds = (
  profile: Language.Profile,
): Language.Profile => {
  const lastId = maxBy(profile.items, "id")?.id ?? 0;

  const { items } = profile.items.reduce<{
    ids: number[];
    duplicatedIds: number[];
    items: Language.ProfileItem[];
  }>(
    (accumulator, item) => {
      if (includes(accumulator.ids, item.id)) {
        accumulator.duplicatedIds.push(item.id);
        accumulator.items.push({
          ...item,
          id: lastId + accumulator.duplicatedIds.length,
        });
        return accumulator;
      }

      accumulator.ids.push(item.id);
      accumulator.items.push(item);
      return accumulator;
    },
    { ids: [], duplicatedIds: [], items: [] },
  );

  return { ...profile, items };
};

export const prepareProfileForEditing = (
  profile: Language.Profile,
): Language.Profile => {
  const cloned = cloneDeep(profile);

  if (cloned.profileType === "enhanced") {
    return cloned;
  }

  return {
    ...repairDuplicateItemIds(cloned),
    tag: cloned.tag || undefined,
  };
};

export const upsertProfile = (
  profiles: readonly Language.Profile[],
  profile: Language.Profile,
): Language.Profile[] => {
  const list = [...profiles];
  const index = list.findIndex((item) => item.profileId === profile.profileId);

  if (index === -1) {
    list.push(profile);
    return list;
  }

  list[index] = profile;
  return list;
};

export const removeProfileAt = (
  profiles: readonly Language.Profile[],
  index: number,
): Language.Profile[] => profiles.filter((_, current) => current !== index);
