import { describe, expect, it } from "vitest";
import {
  serializeProfiles,
  serializeProfileSubmission,
} from "./profileSerialization";

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
  it("serializes every profile in order as enhanced groups", () => {
    const payload = serializeProfiles([
      enhancedProfile,
      { ...enhancedProfile, profileId: 5 },
    ]);
    const parsed = JSON.parse(payload) as Record<string, unknown>[];

    expect(parsed).toHaveLength(2);
    expect(parsed[0].items).toEqual({ groups: expect.any(Array) });
    expect(parsed[1]).not.toHaveProperty("groups");
  });
});
