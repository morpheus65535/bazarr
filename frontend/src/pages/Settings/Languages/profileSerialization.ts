import { snakeCaseKeys } from "@/utilities/case";

// Wire format for the settings endpoint. Profiles send their groups instead of a flat item list.
export const serializeProfileSubmission = (
  profile: Language.Profile,
): Language.RawProfileSubmission => {
  const { groups, ...profileWithoutGroups } = profile;

  return {
    ...profileWithoutGroups,
    items: {
      groups: snakeCaseKeys(groups) as unknown as Language.RawEnhancedGroup[],
    },
  };
};

export const serializeProfiles = (
  profiles: readonly Language.Profile[],
): string => JSON.stringify(profiles.map(serializeProfileSubmission));
