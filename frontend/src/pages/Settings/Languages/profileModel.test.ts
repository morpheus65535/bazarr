import { describe, expect, it } from "vitest";
import { anyCutoff } from "@/components/forms/profileOptions";
import {
  createEnhancedProfile,
  isLanguageRepeated,
  nextGroupId,
  nextItemId,
  nextProfileId,
  removeProfileAt,
  upsertProfile,
} from "./profileModel";

const item = (id: number, language: string): Language.ProfileItem => ({
  id,
  language,
  audioExclude: "False",
  audioOnlyInclude: "False",
  hi: "False",
  forced: "False",
});

const profile = (profileId: number): Language.Profile => ({
  profileId,
  name: `Profile ${profileId}`,
  tag: undefined,
  profileType: "enhanced",
  items: [item(1, "en")],
  groups: [{ id: 1, operator: "AND", items: [item(1, "en")] }],
  cutoff: null,
  mustContain: [],
  mustNotContain: [],
  originalFormat: false,
});

describe("id allocation", () => {
  it("returns the next free profile id", () => {
    expect(nextProfileId([profile(2), profile(7)])).toBe(8);
  });

  it("returns the next free item id across every group", () => {
    expect(nextItemId([item(1, "en"), item(5, "fr")])).toBe(6);
  });

  it("never allocates the reserved any-group cutoff id", () => {
    const groups: Language.EnhancedGroup[] = [
      { id: anyCutoff - 1, operator: "AND", items: [] },
    ];

    expect(nextGroupId(groups)).toBe(anyCutoff + 1);
  });
});

describe("isLanguageRepeated", () => {
  it("treats the same language with a different subtitle type as distinct", () => {
    const normal = item(1, "en");
    const hearingImpaired: Language.ProfileItem = {
      ...item(2, "en"),
      hi: "True",
    };

    expect(isLanguageRepeated([normal, hearingImpaired])).toBe(false);
  });

  it("flags the same language and subtitle type twice", () => {
    expect(isLanguageRepeated([item(1, "en"), item(2, "en")])).toBe(true);
  });
});

describe("createEnhancedProfile", () => {
  it("starts with one AND requirement and no cutoff", () => {
    const created = createEnhancedProfile(4, "en");

    expect(created.profileType).toBe("enhanced");
    expect(created.cutoff).toBeNull();
    expect(created.groups).toEqual([
      { id: 1, operator: "AND", items: [item(1, "en")] },
    ]);
    expect(created.items).toEqual([item(1, "en")]);
  });
});

describe("upsertProfile", () => {
  it("appends a profile that does not exist yet", () => {
    const list = upsertProfile([profile(1)], profile(2));

    expect(list.map((value) => value.profileId)).toEqual([1, 2]);
  });

  it("replaces a profile with a matching id in place", () => {
    const updated = { ...profile(1), name: "Renamed" };
    const list = upsertProfile([profile(1), profile(2)], updated);

    expect(list).toHaveLength(2);
    expect(list[0].name).toBe("Renamed");
    expect(list[1].profileId).toBe(2);
  });
});

describe("removeProfileAt", () => {
  it("removes only the profile at the given index", () => {
    const list = removeProfileAt([profile(1), profile(2), profile(3)], 1);

    expect(list.map((value) => value.profileId)).toEqual([1, 3]);
  });
});
