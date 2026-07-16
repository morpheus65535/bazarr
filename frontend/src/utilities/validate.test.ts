import { describe, expect, it } from "vitest";
import { isEpisode, isMovie, isSeries } from "@/utilities/validate";

describe("validate utilities", () => {
  describe("isMovie", () => {
    it("returns true when the object has a radarrId", () => {
      expect(isMovie({ radarrId: 1 })).toBe(true);
    });

    it("returns false when the object does not have a radarrId", () => {
      expect(isMovie({ sonarrEpisodeId: 1 })).toBe(false);
    });
  });

  describe("isEpisode", () => {
    it("returns true when the object has a sonarrEpisodeId", () => {
      expect(isEpisode({ sonarrEpisodeId: 1 })).toBe(true);
    });

    it("returns false when the object does not have a sonarrEpisodeId", () => {
      expect(isEpisode({ radarrId: 1 })).toBe(false);
    });
  });

  describe("isSeries", () => {
    it("returns true when the object has an episodeFileCount", () => {
      expect(isSeries({ episodeFileCount: 5 })).toBe(true);
    });

    it("returns false when the object does not have an episodeFileCount", () => {
      expect(isSeries({ radarrId: 1 })).toBe(false);
    });
  });
});
