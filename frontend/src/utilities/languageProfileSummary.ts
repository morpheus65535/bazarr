import { anyCutoff } from "@/components/forms/profileOptions";
import { LanguageNameResolver } from "@/utilities/languages";

// Plain-language summaries of a languages profile configuration. These describe
// configuration only; they never claim a subtitle will be downloaded.

export interface RequirementSummary {
  /** "Requirement" for the first group, "Additional requirement" afterwards. */
  label: string;
  operator: "AND" | "OR";
  /** Languages joined with the relationship word, e.g. "English and Portuguese". */
  languages: string;
  /** Full sentence describing the requirement. */
  text: string;
}

export interface LanguageProfileSummary {
  isEnhanced: boolean;
  requirements: RequirementSummary[];
  completion: string;
  caveats: string[];
  restrictions: string[];
}

export const isAudioConditional = (item: Language.ProfileItem): boolean =>
  item.audioOnlyInclude === "True" || item.audioExclude === "True";

const subtitleTypePhrase = (item: Language.ProfileItem): string | undefined => {
  if (item.forced === "True") {
    return "forced";
  }

  if (item.hi === "True") {
    return "hearing-impaired";
  }

  if (item.hi === "Excluded") {
    return "non hearing-impaired";
  }

  return undefined;
};

const audioConditionPhrase = (
  item: Language.ProfileItem,
): string | undefined => {
  if (item.audioOnlyInclude === "True") {
    return "when a matching audio track is present";
  }

  if (item.audioExclude === "True") {
    return "when no matching audio track is present";
  }

  return undefined;
};

export const describeLanguage = (
  item: Language.ProfileItem,
  resolveLanguageName: LanguageNameResolver,
): string => {
  const name = resolveLanguageName(item.language);
  const type = subtitleTypePhrase(item);

  return type ? `${name} (${type})` : name;
};

export const describeLanguageCondition = (
  item: Language.ProfileItem,
  resolveLanguageName: LanguageNameResolver,
): string | undefined => {
  const condition = audioConditionPhrase(item);

  return condition
    ? `${resolveLanguageName(item.language)} is only searched ${condition}.`
    : undefined;
};

export const describeGroupLanguages = (
  group: Language.EnhancedGroup,
  resolveLanguageName: LanguageNameResolver,
): string => {
  const languages = group.items.map((item) =>
    describeLanguage(item, resolveLanguageName),
  );

  if (languages.length === 0) {
    return "no languages";
  }

  if (languages.length === 1) {
    return languages[0];
  }

  return languages.join(group.operator === "AND" ? " and " : " or ");
};

const requirementSentence = (
  operator: Language.EnhancedGroup["operator"],
  languages: string,
): string =>
  operator === "OR"
    ? `Any one of ${languages} subtitles is required.`
    : `${languages} subtitles are required.`;

const groupItems = (
  profile: Language.Profile,
  groups: readonly Language.EnhancedGroup[],
): Language.ProfileItem[] =>
  profile.profileType === "enhanced"
    ? groups.flatMap((group) => group.items)
    : profile.items;

const completionSentence = (
  profile: Language.Profile,
  groups: readonly Language.EnhancedGroup[],
  resolveLanguageName: LanguageNameResolver,
): string => {
  const { cutoff } = profile;

  if (cutoff === null) {
    return "Keep searching until every unmet requirement is satisfied.";
  }

  if (profile.profileType === "enhanced") {
    if (cutoff === anyCutoff) {
      return "Stop searching as soon as any requirement is satisfied.";
    }

    const group = groups.find((value) => value.id === cutoff);

    return group
      ? `Stop searching once ${describeGroupLanguages(group, resolveLanguageName)} is satisfied.`
      : "Stop searching once the selected requirement is satisfied.";
  }

  if (cutoff === anyCutoff) {
    return "Stop searching as soon as any of these languages is found.";
  }

  const item = profile.items.find((value) => value.id === cutoff);

  return item
    ? `Stop searching once ${describeLanguage(item, resolveLanguageName)} subtitles are found.`
    : "Stop searching once the selected language is found.";
};

const summaryCaveats = (
  profile: Language.Profile,
  groups: readonly Language.EnhancedGroup[],
): string[] => {
  const caveats: string[] = [];

  if (groupItems(profile, groups).some(isAudioConditional)) {
    caveats.push(
      "A requirement with an audio condition counts as satisfied when the audio track does not match, even without downloading a subtitle.",
    );
  }

  if (profile.cutoff !== null) {
    caveats.push(
      "Satisfying the stopping rule ends all remaining searches, not only later requirements.",
    );
  }

  return caveats;
};

export const restrictionSummaries = (profile: Language.Profile): string[] => {
  const restrictions: string[] = [];

  if (profile.tag) {
    restrictions.push(`Applies to the "${profile.tag}" tag`);
  }

  if (profile.mustContain.length > 0) {
    restrictions.push(
      `Release name must contain: ${profile.mustContain.join(", ")}`,
    );
  }

  if (profile.mustNotContain.length > 0) {
    restrictions.push(
      `Release name must not contain: ${profile.mustNotContain.join(", ")}`,
    );
  }

  if (profile.originalFormat) {
    restrictions.push("Keep the original subtitle format");
  }

  return restrictions;
};

export const summarizeProfile = (
  profile: Language.Profile,
  resolveLanguageName: LanguageNameResolver,
): LanguageProfileSummary => {
  const isEnhanced = profile.profileType === "enhanced";

  const groups: Language.EnhancedGroup[] = isEnhanced
    ? (profile.groups ?? [])
    : [{ id: 0, operator: "AND", items: profile.items }];

  const requirements = groups.map((group, index) => {
    const languages = describeGroupLanguages(group, resolveLanguageName);

    return {
      label: index === 0 ? "Requirement" : "Additional requirement",
      operator: group.operator,
      languages,
      text: requirementSentence(group.operator, languages),
    };
  });

  return {
    isEnhanced,
    requirements,
    completion: completionSentence(profile, groups, resolveLanguageName),
    caveats: summaryCaveats(profile, groups),
    restrictions: restrictionSummaries(profile),
  };
};
