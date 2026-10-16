import { SelectorOption } from "@/components";

// Shared by the languages profile editor and the profile rules display.

// Cutoff value meaning "any language" for basic profiles and "any group" for enhanced ones.
export const anyCutoff = 65535;

export const subtitlesTypeOptions: SelectorOption<string>[] = [
  {
    label: "Full subtitles · hearing-impaired allowed",
    value: "normal",
  },
  {
    label: "Hearing-impaired required",
    value: "hi",
  },
  {
    label: "Exclude hearing-impaired",
    value: "nonHi",
  },
  {
    label: "Forced subtitles · foreign dialogue only",
    value: "forced",
  },
];

export const inclusionOptions: SelectorOption<string>[] = [
  {
    label: "Always",
    value: "always_include",
  },
  {
    label: "Only when a matching audio track is present",
    value: "audioOnlyInclude",
  },
  {
    label: "Only when no matching audio track is present",
    value: "audioExclude",
  },
];

// Readable relationship wording for the AND/OR operator stored on each group.
export const relationshipOptions: SelectorOption<string>[] = [
  {
    label: "All languages",
    value: "AND",
  },
  {
    label: "Any language",
    value: "OR",
  },
];

export const subtitleTypeValue = (item: Language.ProfileItem): string => {
  if (item.forced === "True") {
    return "forced";
  }

  if (item.hi === "True") {
    return "hi";
  }

  if (item.hi === "Excluded") {
    return "nonHi";
  }

  return "normal";
};

export const subtitleTypePatch = (
  value: string,
): Partial<Language.ProfileItem> => ({
  hi: value === "hi" ? "True" : value === "nonHi" ? "Excluded" : "False",
  forced: value === "forced" ? "True" : "False",
});

export const inclusionValue = (item: Language.ProfileItem): string => {
  if (item.audioExclude === "True") {
    return "audioExclude";
  }

  if (item.audioOnlyInclude === "True") {
    return "audioOnlyInclude";
  }

  return "always_include";
};

export const inclusionPatch = (
  value: string,
): Partial<Language.ProfileItem> => ({
  audioExclude: value === "audioExclude" ? "True" : "False",
  audioOnlyInclude: value === "audioOnlyInclude" ? "True" : "False",
});

// Compact label used by the profile rules display, e.g. "en:HI" or "fr:Forced".
export const itemLabel = (item: Language.ProfileItem): string =>
  item.language +
  (item.hi === "True"
    ? ":HI"
    : item.forced === "True"
      ? ":Forced"
      : item.hi === "Excluded"
        ? ":Non-HI"
        : "");
