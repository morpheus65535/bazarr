import { describe, it } from "vitest";
import { StaticModals } from "./WithModal";

describe("modal tests", () => {
  it.skip("no duplicated modals", () => {
    const existedKeys = new Set<string>();
    StaticModals.forEach(({ modalKey }) => {
      expect(existedKeys.has(modalKey)).toBeFalsy();
      existedKeys.add(modalKey);
    });
  });
});
