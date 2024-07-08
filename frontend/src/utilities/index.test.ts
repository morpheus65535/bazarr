import { fromPython, toPython } from "@/utilities/index";

describe("fromPythonConversion", () => {
  it("should convert a true value", () => {
    expect(fromPython("True")).toBe(true);
  });

  it("should convert a false value", () => {
    expect(fromPython("False")).toBe(false);
  });

  it("should convert an undefined value", () => {
    expect(fromPython(undefined)).toBe(false);
  });
});

describe("toPythonConversion", () => {
  it("should convert a true value", () => {
    expect(toPython(true)).toBe("True");
  });

  it("should convert a false value", () => {
    expect(toPython(false)).toBe("False");
  });
});
