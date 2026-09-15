import { describe, expect, it, vitest } from "vitest";
import { useLanguageProfiles } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import LanguageProfile from "./LanguageProfile";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return { ...actual, useLanguageProfiles: vitest.fn() };
});

const mockUseLanguageProfiles = vitest.mocked(useLanguageProfiles);

describe("LanguageProfile", () => {
  it("renders the matching profile name", () => {
    mockUseLanguageProfiles.mockReturnValue({
      data: [{ profileId: 1, name: "English" }],
    } as unknown as ReturnType<typeof useLanguageProfiles>);

    customRender(<LanguageProfile index={1} />);

    expect(screen.getByText("English")).toBeInTheDocument();
  });

  it("renders the default empty text when no profile matches", () => {
    mockUseLanguageProfiles.mockReturnValue({
      data: [{ profileId: 1, name: "English" }],
    } as unknown as ReturnType<typeof useLanguageProfiles>);

    customRender(<LanguageProfile index={2} />);

    expect(screen.getByText("Unknown Profile")).toBeInTheDocument();
  });

  it("renders custom empty text when index is null", () => {
    mockUseLanguageProfiles.mockReturnValue({
      data: undefined,
    } as unknown as ReturnType<typeof useLanguageProfiles>);

    customRender(<LanguageProfile index={null} empty="None" />);

    expect(screen.getByText("None")).toBeInTheDocument();
  });
});
