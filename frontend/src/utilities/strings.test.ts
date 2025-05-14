import { describe, expect, it } from "vitest";
import { capitalize } from "./strings";

describe("capitalize", () => {
  it("should capitalize the first letter of a string", () => {
    expect(capitalize("hello")).toBe("Hello");
    expect(capitalize("world")).toBe("World");
  });

  it("should return an empty string if given an empty string", () => {
    expect(capitalize("")).toBe("");
  });

  it("should handle already capitalized strings", () => {
    expect(capitalize("Hello")).toBe("Hello");
    expect(capitalize("World")).toBe("World");
  });

  it("should handle single character strings", () => {
    expect(capitalize("a")).toBe("A");
    expect(capitalize("z")).toBe("Z");
  });

  it("should keep subsequent capital letters unchanged", () => {
    expect(capitalize("javaScript")).toBe("Javascript");
    expect(capitalize("reactJS")).toBe("Reactjs");
  });

  it("should handle strings with leading spaces", () => {
    expect(capitalize(" hello")).toBe(" hello");
    expect(capitalize("  world")).toBe("  world");
  });

  it("should handle non-letter characters at the beginning", () => {
    expect(capitalize("123abc")).toBe("123abc");
    expect(capitalize("!test")).toBe("!test");
  });
});
