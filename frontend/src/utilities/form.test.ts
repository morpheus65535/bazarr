import { describe, expect, it } from "vitest";
import FormUtils from "@/utilities/form";

describe("FormUtils", () => {
  describe("validation", () => {
    it("returns null when the condition passes", () => {
      const validator = FormUtils.validation(
        (value: string) => value.length > 0,
        "required",
      );

      expect(validator("hello")).toBeNull();
    });

    it("returns the error message when the condition fails", () => {
      const validator = FormUtils.validation(
        (value: string) => value.length > 0,
        "required",
      );

      expect(validator("")).toBe("required");
    });
  });
});
