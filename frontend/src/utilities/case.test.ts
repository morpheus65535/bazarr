import { describe, expect, it } from "vitest";
import {
  camelCaseKeys,
  snakeCaseKeys,
  toCamelCase,
  toSnakeCase,
} from "@/utilities/case";

describe("case utilities", () => {
  describe("toCamelCase", () => {
    it("converts snake_case to camelCase", () => {
      expect(toCamelCase("subs_id")).toBe("subsId");
      expect(toCamelCase("subtitles_path")).toBe("subtitlesPath");
      expect(toCamelCase("episode_number")).toBe("episodeNumber");
    });

    it("leaves camelCase unchanged", () => {
      expect(toCamelCase("provider")).toBe("provider");
      expect(toCamelCase("radarrId")).toBe("radarrId");
    });
  });

  describe("toSnakeCase", () => {
    it("converts camelCase to snake_case", () => {
      expect(toSnakeCase("subsId")).toBe("subs_id");
      expect(toSnakeCase("subtitlesPath")).toBe("subtitles_path");
      expect(toSnakeCase("episodeNumber")).toBe("episode_number");
    });

    it("leaves snake_case unchanged", () => {
      expect(toSnakeCase("provider")).toBe("provider");
    });
  });

  describe("camelCaseKeys", () => {
    it("maps object keys recursively", () => {
      const result = camelCaseKeys({
        data: [
          {
            subs_id: "123",
            parsed_timestamp: "now",
            dont_matches: ["a"],
            nested: { raw_value: 1 },
          },
        ],
        total: 1,
      });

      expect(result).toEqual({
        data: [
          {
            subsId: "123",
            parsedTimestamp: "now",
            dontMatches: ["a"],
            nested: { rawValue: 1 },
          },
        ],
        total: 1,
      });
    });

    it("leaves non-object values unchanged", () => {
      const date = new Date("2024-01-01");
      const result = camelCaseKeys({ created_at: date, count: 5 });

      expect(result.createdAt).toBe(date);
      expect(result.count).toBe(5);
    });
  });

  describe("snakeCaseKeys", () => {
    it("maps object keys recursively", () => {
      const result = snakeCaseKeys({
        subsId: "123",
        subtitlesPath: "/path",
        nested: { camelCaseValue: 1 },
      });

      expect(result).toEqual({
        subs_id: "123",
        subtitles_path: "/path",
        nested: { camel_case_value: 1 },
      });
    });
  });
});
