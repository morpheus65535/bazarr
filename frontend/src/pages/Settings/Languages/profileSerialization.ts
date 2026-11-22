import { snakeCaseKeys } from "@/utilities/case";

// Wire format for the settings endpoint. Enhanced profiles send their groups;
// basic and legacy profiles send their flat item list.
export const serializeProfileSubmission = (
  profile: Language.Profile,
): Language.RawProfileSubmission => {
  const { groups, ...profileWithoutGroups } = profile;

  const items =
    profile.profileType === "enhanced" && groups
      ? {
          groups: snakeCaseKeys(
            groups,
          ) as unknown as Language.RawEnhancedGroup[],
        }
      : profile.items.map(
          (item) => snakeCaseKeys(item) as unknown as Language.RawProfileItem,
        );

  return { ...profileWithoutGroups, items };
};

export const serializeProfiles = (
  profiles: readonly Language.Profile[],
): string => JSON.stringify(profiles.map(serializeProfileSubmission));
