import { describe, expect, it } from "vitest";
import { buildListParams } from "./utils";

describe("buildListParams", () => {
  it("keeps the paging fields", () => {
    expect(buildListParams({ start: 10, length: 25 })).toEqual({
      start: 10,
      length: 25,
    });
  });

  it("maps sort and filters to backend params", () => {
    expect(
      buildListParams({
        start: 0,
        length: 25,
        sortBy: "title",
        sortOrder: "desc",
        filters: {
          monitored: true,
          missing: false,
          profileId: 3,
          audioLanguage: "English",
          tags: ["a", "b"],
        },
      }),
    ).toEqual({
      start: 0,
      length: 25,
      sort_by: "title",
      sort_order: "desc",
      monitored: "true",
      missing: "false",
      profileid: 3,
      audio_language: "English",
      tags: ["a", "b"],
    });
  });

  it("maps profileId 0 to none", () => {
    expect(
      buildListParams({ start: 0, length: 25, filters: { profileId: 0 } })
        .profileid,
    ).toBe("none");
  });

  it("drops undefined values and empty tags", () => {
    expect(
      buildListParams({
        start: 0,
        length: 25,
        filters: { tags: [] },
      }),
    ).toEqual({ start: 0, length: 25 });
  });
});
