import { describe, expect, it, vitest } from "vitest";
import { useLanguages } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import LanguageSelector from "./LanguageSelector";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return { ...actual, useLanguages: vitest.fn() };
});

const mockUseLanguages = vitest.mocked(useLanguages);

describe("LanguageSelector", () => {
  it("renders all languages", () => {
    mockUseLanguages.mockReturnValue({
      data: [
        { code3: "eng", name: "English", enabled: true },
        { code3: "fra", name: "French", enabled: false },
      ],
    } as unknown as ReturnType<typeof useLanguages>);

    customRender(<LanguageSelector />);

    expect(screen.getByText("English")).toBeInTheDocument();
    expect(screen.getByText("French")).toBeInTheDocument();
  });

  it("renders only enabled languages when enabled prop is true", () => {
    mockUseLanguages.mockReturnValue({
      data: [
        { code3: "eng", name: "English", enabled: true },
        { code3: "fra", name: "French", enabled: false },
      ],
    } as unknown as ReturnType<typeof useLanguages>);

    customRender(<LanguageSelector enabled />);

    expect(screen.getByText("English")).toBeInTheDocument();
    expect(screen.queryByText("French")).not.toBeInTheDocument();
  });
});
