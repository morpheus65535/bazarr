import { describe, expect, it } from "vitest";
import {
  serializeProfiles,
  serializeProfileSubmission,
} from "./profileSerialization";

const basicProfile: Language.Profile = {
  profileId: 1,
  name: "Basic",
  tag: "mytag",
  items: [
    {
      id: 1,
      language: "en",
      audioExclude: "False",
      audioOnlyInclude: "False",
      hi: "False",
      forced: "False",
    },
  ],
  cutoff: 1,
  mustContain: ["x265"],
  mustNotContain: [],
  originalFormat: true,
};

const legacyProfile: Language.Profile = {
  profileId: 2,
  name: "Legacy",
  tag: undefined,
  items: [
    {
      id: 4,
      language: "fr",
      audioExclude: "True",
      audioOnlyInclude: "False",
      hi: "Excluded",
      forced: "False",
    },
  ],
  cutoff: null,
  mustContain: [],
  mustNotContain: [],
  originalFormat: false,
};

const enhancedProfile: Language.Profile = {
  profileId: 3,
  name: "Enhanced",
  tag: undefined,
  profileType: "enhanced",
  items: [
    {
      id: 1,
      language: "en",
      audioExclude: "False",
      audioOnlyInclude: "False",
      hi: "False",
      forced: "False",
    },
  ],
  groups: [
    {
      id: 1,
      operator: "AND",
      items: [
        {
          id: 1,
          language: "en",
          audioExclude: "False",
          audioOnlyInclude: "False",
          hi: "False",
          forced: "False",
        },
      ],
    },
  ],
  cutoff: 1,
  mustContain: [],
  mustNotContain: [],
  originalFormat: false,
};

describe("serializeProfileSubmission", () => {
  it("sends a basic profile as a flat item list with snake case keys", () => {
    const submission = serializeProfileSubmission(basicProfile);

    expect(submission).toMatchObject({
      profileId: 1,
      name: "Basic",
      cutoff: 1,
      mustContain: ["x265"],
      originalFormat: true,
    });
    expect(submission.items).toEqual([
      {
        id: 1,
        language: "en",
        audio_exclude: "False",
        audio_only_include: "False",
        hi: "False",
        forced: "False",
      },
    ]);
  });

  it("keeps a legacy untyped profile flat and without a profile type", () => {
    const submission = serializeProfileSubmission(legacyProfile);

    expect(submission).not.toHaveProperty("profileType");
    expect(Array.isArray(submission.items)).toBe(true);
    expect(submission.items).toEqual([
      {
        id: 4,
        language: "fr",
        audio_exclude: "True",
        audio_only_include: "False",
        hi: "Excluded",
        forced: "False",
      },
    ]);
  });

  it("sends an enhanced profile as groups and drops the derived flat items", () => {
    const submission = serializeProfileSubmission(enhancedProfile);

    expect(submission).not.toHaveProperty("groups");
    expect(submission.items).toEqual({
      groups: [
        {
          id: 1,
          operator: "AND",
          items: [
            {
              id: 1,
              language: "en",
              audio_exclude: "False",
              audio_only_include: "False",
              hi: "False",
              forced: "False",
            },
          ],
        },
      ],
    });
  });
});

describe("serializeProfiles", () => {
  it("serializes every profile in order without mixing representations", () => {
    const payload = serializeProfiles([basicProfile, enhancedProfile]);
    const parsed = JSON.parse(payload) as Record<string, unknown>[];

    expect(parsed).toHaveLength(2);
    expect(Array.isArray(parsed[0].items)).toBe(true);
    expect(parsed[1].items).toEqual({ groups: expect.any(Array) });
    expect(parsed[1]).not.toHaveProperty("groups");
  });
});
