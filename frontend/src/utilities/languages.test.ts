import { renderHook } from "@testing-library/react";
import { describe, expect, it, vitest } from "vitest";
import { useLanguageProfiles, useLanguages } from "@/apis/hooks";
import {
  normalizeAudioLanguage,
  useEnabledLanguages,
  useLanguageFromCode3,
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "@/utilities/languages";

vitest.mock("@/apis/hooks", () => ({
  useLanguages: vitest.fn(),
  useLanguageProfiles: vitest.fn(),
}));

const mockUseLanguages = vitest.mocked(useLanguages);
const mockUseLanguageProfiles = vitest.mocked(useLanguageProfiles);

describe("languages utilities", () => {
  describe("useLanguageProfileBy", () => {
    it("returns the matching profile", () => {
      mockUseLanguageProfiles.mockReturnValue({
        data: [
          { profileId: 1, name: "English" },
          { profileId: 2, name: "French" },
        ],
      } as unknown as ReturnType<typeof useLanguageProfiles>);

      const { result } = renderHook(() => useLanguageProfileBy(1));

      expect(result.current).toEqual({ profileId: 1, name: "English" });
    });

    it("returns undefined when no profile matches", () => {
      mockUseLanguageProfiles.mockReturnValue({
        data: [{ profileId: 1, name: "English" }],
      } as unknown as ReturnType<typeof useLanguageProfiles>);

      const { result } = renderHook(() => useLanguageProfileBy(2));

      expect(result.current).toBeUndefined();
    });

    it("returns undefined when id is undefined", () => {
      mockUseLanguageProfiles.mockReturnValue({
        data: [{ profileId: 1, name: "English" }],
      } as unknown as ReturnType<typeof useLanguageProfiles>);

      const { result } = renderHook(() => useLanguageProfileBy(undefined));

      expect(result.current).toBeUndefined();
    });
  });

  describe("useEnabledLanguages", () => {
    it("returns only enabled languages", () => {
      mockUseLanguages.mockReturnValue({
        data: [
          { code2: "en", name: "English", enabled: true },
          { code2: "fr", name: "French", enabled: false },
        ],
      } as unknown as ReturnType<typeof useLanguages>);

      const { result } = renderHook(() => useEnabledLanguages());

      expect(result.current.data).toEqual([{ code2: "en", name: "English" }]);
    });

    it("returns an empty array when languages data is undefined", () => {
      mockUseLanguages.mockReturnValue({
        data: undefined,
      } as unknown as ReturnType<typeof useLanguages>);

      const { result } = renderHook(() => useEnabledLanguages());

      expect(result.current.data).toEqual([]);
    });
  });

  describe("useProfileItemsToLanguages", () => {
    it("maps profile items to language info", () => {
      mockUseLanguages.mockReturnValue({
        data: [
          { code2: "en", name: "English", code3: "eng" },
          { code2: "fr", name: "French", code3: "fra" },
        ],
      } as unknown as ReturnType<typeof useLanguages>);

      const profile = {
        items: [
          { language: "en", hi: "True", forced: "False" },
          { language: "fr", hi: "False", forced: "True" },
        ],
      } as Language.Profile;

      const { result } = renderHook(() => useProfileItemsToLanguages(profile));

      expect(result.current).toEqual([
        { code2: "en", name: "English", hi: true, forced: false },
        { code2: "fr", name: "French", hi: false, forced: true },
      ]);
    });

    it("returns an empty array when profile is undefined", () => {
      mockUseLanguages.mockReturnValue({
        data: [],
      } as unknown as ReturnType<typeof useLanguages>);

      const { result } = renderHook(() =>
        useProfileItemsToLanguages(undefined),
      );

      expect(result.current).toEqual([]);
    });
  });

  describe("useLanguageFromCode3", () => {
    it("returns the matching language", () => {
      mockUseLanguages.mockReturnValue({
        data: [
          { code2: "en", name: "English", code3: "eng" },
          { code2: "fr", name: "French", code3: "fra" },
        ],
      } as unknown as ReturnType<typeof useLanguages>);

      const { result } = renderHook(() => useLanguageFromCode3("fra"));

      expect(result.current).toEqual({
        code2: "fr",
        name: "French",
        code3: "fra",
      });
    });
  });

  describe("normalizeAudioLanguage", () => {
    it("normalizes Chinese Simplified to Chinese", () => {
      expect(normalizeAudioLanguage("Chinese Simplified")).toBe("Chinese");
    });

    it("leaves other names unchanged", () => {
      expect(normalizeAudioLanguage("English")).toBe("English");
    });
  });
});
