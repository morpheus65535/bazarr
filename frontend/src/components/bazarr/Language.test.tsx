import { rawRender, screen } from "@/tests";
import { Language } from ".";

import { describe, it } from "vitest";

describe("Language text", () => {
  const testLanguage: Language.Info = {
    code2: "en",
    name: "English",
  };

  it("should show short text", () => {
    rawRender(<Language.Text value={testLanguage}></Language.Text>);

    expect(screen.getByText(testLanguage.code2)).toBeDefined();
  });

  it("should show long text", () => {
    rawRender(<Language.Text value={testLanguage} long></Language.Text>);

    expect(screen.getByText(testLanguage.name)).toBeDefined();
  });

  const testLanguageWithHi: Language.Info = { ...testLanguage, hi: true };

  it("should show short text with HI", () => {
    rawRender(<Language.Text value={testLanguageWithHi}></Language.Text>);

    const expectedText = `${testLanguageWithHi.code2}:HI`;

    expect(screen.getByText(expectedText)).toBeDefined();
  });

  it("should show long text with HI", () => {
    rawRender(<Language.Text value={testLanguageWithHi} long></Language.Text>);

    const expectedText = `${testLanguageWithHi.name} HI`;

    expect(screen.getByText(expectedText)).toBeDefined();
  });

  const testLanguageWithForced: Language.Info = {
    ...testLanguage,
    forced: true,
  };

  it("should show short text with Forced", () => {
    rawRender(<Language.Text value={testLanguageWithForced}></Language.Text>);

    const expectedText = `${testLanguageWithHi.code2}:Forced`;

    expect(screen.getByText(expectedText)).toBeDefined();
  });

  it("should show long text with Forced", () => {
    rawRender(
      <Language.Text value={testLanguageWithForced} long></Language.Text>,
    );

    const expectedText = `${testLanguageWithHi.name} Forced`;

    expect(screen.getByText(expectedText)).toBeDefined();
  });
});

describe("Language list", () => {
  const elements: Language.Info[] = [
    {
      code2: "en",
      name: "English",
    },
    {
      code2: "zh",
      name: "Chinese",
    },
  ];

  it("should show all languages", () => {
    rawRender(<Language.List value={elements}></Language.List>);

    elements.forEach((value) => {
      expect(screen.getByText(value.name)).toBeDefined();
    });
  });
});
