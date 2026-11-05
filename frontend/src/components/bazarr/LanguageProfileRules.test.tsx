import { describe, expect, it } from "vitest";
import { customRender, screen } from "@/tests";
import LanguageProfileRules from "./LanguageProfileRules";

const item = (
  id: number,
  language: string,
  overrides: Partial<Language.ProfileItem> = {},
): Language.ProfileItem => ({
  id,
  language,
  audioExclude: "False",
  audioOnlyInclude: "False",
  hi: "False",
  forced: "False",
  ...overrides,
});

describe("LanguageProfileRules", () => {
  it("renders an enhanced profile as readable groups", () => {
    customRender(
      <LanguageProfileRules
        profile={{
          profileType: "enhanced",
          cutoff: 1,
          items: [],
          groups: [
            {
              id: 1,
              operator: "AND",
              items: [item(1, "en"), item(2, "fr")],
            },
            {
              id: 2,
              operator: "OR",
              items: [item(3, "de"), item(4, "it")],
            },
          ],
        }}
      ></LanguageProfileRules>,
    );

    expect(screen.getByText("All of")).toBeInTheDocument();
    expect(screen.getByText("Any of")).toBeInTheDocument();
    expect(screen.getByText("de")).toBeInTheDocument();
    expect(screen.getByText("it")).toBeInTheDocument();
  });

  it("marks the cutoff group", () => {
    customRender(
      <LanguageProfileRules
        profile={{
          profileType: "enhanced",
          cutoff: 1,
          items: [],
          groups: [
            { id: 1, operator: "AND", items: [item(1, "en")] },
            { id: 2, operator: "OR", items: [item(2, "fr")] },
          ],
        }}
      ></LanguageProfileRules>,
    );

    const badge = screen.getByTitle("Stops searching once this is found");

    expect(badge).toHaveTextContent("en");
  });

  it("renders a basic profile as language badges and highlights its cutoff", () => {
    customRender(
      <LanguageProfileRules
        profile={{
          profileType: "basic",
          cutoff: 2,
          items: [item(1, "en"), item(2, "fr", { hi: "True" })],
        }}
      ></LanguageProfileRules>,
    );

    expect(screen.getByText("fr:HI")).toBeInTheDocument();
    expect(
      screen.getByTitle("Stops searching once this is found"),
    ).toHaveTextContent("fr:HI");
  });
});
