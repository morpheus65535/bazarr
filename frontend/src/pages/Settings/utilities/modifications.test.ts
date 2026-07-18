import { describe, expect, it } from "vitest";
import {
  SubzeroColorModification,
  SubzeroModification,
} from "@/pages/Settings/utilities/modifications";

describe("modifications utilities", () => {
  describe("SubzeroModification", () => {
    it("returns true when the modifier is present", () => {
      expect(
        SubzeroModification("shift")({
          general: { subzero_mods: ["shift"] },
        } as Settings),
      ).toBe(true);
    });

    it("returns false when the modifier is absent", () => {
      expect(
        SubzeroModification("shift")({
          general: { subzero_mods: ["color"] },
        } as Settings),
      ).toBe(false);
    });

    it("returns false when subzero_mods is undefined", () => {
      expect(
        SubzeroModification("shift")({
          general: {},
        } as Settings),
      ).toBe(false);
    });
  });

  describe("SubzeroColorModification", () => {
    it("returns the matching color modifier", () => {
      expect(
        SubzeroColorModification({
          general: { subzero_mods: ["shift", "color:blue"] },
        } as Settings),
      ).toBe("color:blue");
    });

    it("returns an empty string when no color modifier is present", () => {
      expect(
        SubzeroColorModification({
          general: { subzero_mods: ["shift"] },
        } as Settings),
      ).toBe("");
    });

    it("returns an empty string when subzero_mods is undefined", () => {
      expect(
        SubzeroColorModification({
          general: {},
        } as Settings),
      ).toBe("");
    });
  });
});
