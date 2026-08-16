// @vitest-environment node
import { describe, expect, it } from "vitest";
import { buildListSearchParams, parseListQuery } from "./listQuery";

describe("parseListQuery", () => {
  it("parses sort and filters", () => {
    const params = new URLSearchParams(
      "sort_by=title&sort_order=desc&monitored=true&missing=false&profileid=3&audio_language=English&tags=a&tags=b",
    );
    expect(parseListQuery(params)).toEqual({
      sortBy: "title",
      sortOrder: "desc",
      filters: {
        monitored: true,
        missing: false,
        profileId: 3,
        audioLanguage: "English",
        tags: ["a", "b"],
      },
    });
  });

  it("parses profileid none as 0", () => {
    const params = new URLSearchParams("profileid=none");
    expect(parseListQuery(params).filters?.profileId).toBe(0);
  });

  it("returns empty state when nothing is set", () => {
    expect(parseListQuery(new URLSearchParams())).toEqual({
      sortBy: undefined,
      sortOrder: undefined,
      filters: undefined,
    });
  });

  it("uses prefixed keys when a prefix is given", () => {
    const params = new URLSearchParams(
      "series_sort_by=title&series_monitored=true&sort_by=other",
    );
    const result = parseListQuery(params, "series");
    expect(result.sortBy).toBe("title");
    expect(result.filters?.monitored).toBe(true);
  });
});

describe("buildListSearchParams", () => {
  it("serializes sort and filters", () => {
    const next = buildListSearchParams(new URLSearchParams(), {
      sortBy: "title",
      sortOrder: "asc",
      filters: {
        monitored: true,
        missing: false,
        profileId: 0,
        audioLanguage: "English",
        tags: ["a", "b"],
      },
    });
    expect(next.get("sort_by")).toBe("title");
    expect(next.get("sort_order")).toBe("asc");
    expect(next.get("monitored")).toBe("true");
    expect(next.get("missing")).toBe("false");
    expect(next.get("profileid")).toBe("none");
    expect(next.get("audio_language")).toBe("English");
    expect(next.getAll("tags")).toEqual(["a", "b"]);
  });

  it("removes keys when values are cleared", () => {
    const prev = new URLSearchParams("sort_by=title&monitored=true&tags=a");
    const next = buildListSearchParams(prev, {});
    expect(next.get("sort_by")).toBeNull();
    expect(next.get("monitored")).toBeNull();
    expect(next.getAll("tags")).toEqual([]);
  });

  it("uses prefixed keys when a prefix is given", () => {
    const next = buildListSearchParams(
      new URLSearchParams(),
      { sortBy: "title" },
      "movies",
    );
    expect(next.get("movies_sort_by")).toBe("title");
    expect(next.get("sort_by")).toBeNull();
  });

  it("keeps unrelated params untouched", () => {
    const prev = new URLSearchParams("page=3&other=1");
    const next = buildListSearchParams(prev, { sortBy: "title" });
    expect(next.get("other")).toBe("1");
    expect(next.get("page")).toBe("3");
  });

  it("roundtrips through parse", () => {
    const state: Parameter.ListState = {
      sortBy: "title",
      sortOrder: "desc",
      filters: { monitored: true, profileId: 0, tags: ["x"] },
    };
    expect(
      parseListQuery(buildListSearchParams(new URLSearchParams(), state)),
    ).toEqual(state);
  });
});
