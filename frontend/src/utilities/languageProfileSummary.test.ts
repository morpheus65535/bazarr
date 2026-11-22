import { describe, expect, it } from "vitest";
import { anyCutoff } from "@/components/forms/profileOptions";
import {
  describeLanguageCondition,
  restrictionSummaries,
  summarizeProfile,
} from "./languageProfileSummary";

const names: Record<string, string> = {
  en: "English",
  pt: "Portuguese",
  fr: "French",
};

const resolveLanguageName = (code: string): string => names[code] ?? code;

const item = (
  id: number,
  language: string,
  overrides: Partial<Language.ProfileItem> = {},
): Language.ProfileItem => ({
  id,
  language,
  audioExclude: "False",
  audioOnlyInclude: "False",
  hi: "False",
  forced: "False",
  ...overrides,
});

const enhancedProfile = (
  overrides: Partial<Language.Profile> = {},
): Language.Profile => ({
  profileId: 1,
  name: "Enhanced",
  tag: undefined,
  profileType: "enhanced",
  items: [],
  groups: [{ id: 1, operator: "AND", items: [item(1, "en"), item(2, "pt")] }],
  cutoff: null,
  mustContain: [],
  mustNotContain: [],
  originalFormat: false,
  ...overrides,
});

const basicProfile = (
  overrides: Partial<Language.Profile> = {},
): Language.Profile => ({
  profileId: 2,
  name: "Basic",
  tag: undefined,
  items: [item(1, "en"), item(2, "fr")],
  cutoff: null,
  mustContain: [],
  mustNotContain: [],
  originalFormat: false,
  ...overrides,
});

describe("summarizeProfile requirements", () => {
  it("describes an AND group as every language being required", () => {
    const summary = summarizeProfile(enhancedProfile(), resolveLanguageName);

    expect(summary.requirements[0].languages).toBe("English and Portuguese");
    expect(summary.requirements[0].text).toBe(
      "English and Portuguese subtitles are required.",
    );
  });

  it("describes an OR group as any one language being enough", () => {
    const summary = summarizeProfile(
      enhancedProfile({
        groups: [
          {
            id: 1,
            operator: "OR",
            items: [item(1, "en"), item(2, "pt")],
          },
        ],
      }),
      resolveLanguageName,
    );

    expect(summary.requirements[0].text).toBe(
      "Any one of English or Portuguese subtitles is required.",
    );
  });

  it("labels later groups as additional requirements", () => {
    const summary = summarizeProfile(
      enhancedProfile({
        groups: [
          { id: 1, operator: "AND", items: [item(1, "en")] },
          { id: 2, operator: "OR", items: [item(2, "fr"), item(3, "pt")] },
        ],
      }),
      resolveLanguageName,
    );

    expect(summary.requirements[0].label).toBe("Requirement");
    expect(summary.requirements[1].label).toBe("Additional requirement");
  });

  it("includes the subtitle type in the language name", () => {
    const summary = summarizeProfile(
      enhancedProfile({
        groups: [
          { id: 1, operator: "AND", items: [item(1, "en", { hi: "True" })] },
        ],
      }),
      resolveLanguageName,
    );

    expect(summary.requirements[0].languages).toBe(
      "English (hearing-impaired)",
    );
  });

  it("falls back to the stored code when a language name is unknown", () => {
    const summary = summarizeProfile(
      enhancedProfile({
        groups: [{ id: 1, operator: "AND", items: [item(1, "xx")] }],
      }),
      resolveLanguageName,
    );

    expect(summary.requirements[0].languages).toBe("xx");
  });
});

describe("summarizeProfile completion", () => {
  it("keeps searching until every requirement is met when there is no cutoff", () => {
    const summary = summarizeProfile(enhancedProfile(), resolveLanguageName);

    expect(summary.completion).toBe(
      "Keep searching until every unmet requirement is satisfied.",
    );
  });

  it("stops on any requirement for the any-group cutoff", () => {
    const summary = summarizeProfile(
      enhancedProfile({ cutoff: anyCutoff }),
      resolveLanguageName,
    );

    expect(summary.completion).toBe(
      "Stop searching as soon as any requirement is satisfied.",
    );
  });

  it("names the selected group for a group cutoff", () => {
    const summary = summarizeProfile(
      enhancedProfile({
        groups: [
          { id: 1, operator: "AND", items: [item(1, "en")] },
          { id: 2, operator: "OR", items: [item(2, "fr"), item(3, "pt")] },
        ],
        cutoff: 2,
      }),
      resolveLanguageName,
    );

    expect(summary.completion).toBe(
      "Stop searching once French or Portuguese is satisfied.",
    );
  });

  it("names the selected language for a basic item cutoff", () => {
    const summary = summarizeProfile(
      basicProfile({ cutoff: 2 }),
      resolveLanguageName,
    );

    expect(summary.completion).toBe(
      "Stop searching once French subtitles are found.",
    );
  });

  it("stops on any language for the basic any cutoff", () => {
    const summary = summarizeProfile(
      basicProfile({ cutoff: anyCutoff }),
      resolveLanguageName,
    );

    expect(summary.completion).toBe(
      "Stop searching as soon as any of these languages is found.",
    );
  });
});

describe("summarizeProfile caveats and restrictions", () => {
  it("explains audio conditions and that a cutoff ends all searches", () => {
    const summary = summarizeProfile(
      enhancedProfile({
        groups: [
          {
            id: 1,
            operator: "AND",
            items: [item(1, "en", { audioOnlyInclude: "True" })],
          },
        ],
        cutoff: 1,
      }),
      resolveLanguageName,
    );

    expect(summary.caveats).toHaveLength(2);
    expect(summary.caveats[0]).toMatch(/audio condition/i);
    expect(summary.caveats[1]).toMatch(/ends all remaining searches/i);
  });

  it("lists active advanced restrictions", () => {
    const restrictions = restrictionSummaries({
      ...enhancedProfile(),
      tag: "kids",
      mustContain: ["x265"],
      mustNotContain: ["cam"],
      originalFormat: true,
    });

    expect(restrictions).toEqual([
      'Applies to the "kids" tag',
      "Release name must contain: x265",
      "Release name must not contain: cam",
      "Keep the original subtitle format",
    ]);
  });
});

describe("describeLanguageCondition", () => {
  it("returns undefined when the language is always searched", () => {
    expect(
      describeLanguageCondition(item(1, "en"), resolveLanguageName),
    ).toBeUndefined();
  });

  it("names the language in the audio condition helper", () => {
    expect(
      describeLanguageCondition(
        item(1, "en", { audioOnlyInclude: "True" }),
        resolveLanguageName,
      ),
    ).toBe("English is only searched when a matching audio track is present.");
  });
});
