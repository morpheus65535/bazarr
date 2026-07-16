import { describe, expect, it, vitest } from "vitest";
import { useOs } from "@mantine/hooks";
import { spotlightApi } from "@/components/AppSpotlight";
import { customRender, screen } from "@/tests";
import userEvent from "@testing-library/user-event";
import Search from "./Search";

vitest.mock("@mantine/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@mantine/hooks")>();
  return { ...actual, useOs: vitest.fn() };
});

const mockUseOs = vitest.mocked(useOs);

describe("Search", () => {
  it("renders the macOS keyboard shortcut", () => {
    mockUseOs.mockReturnValue("macos");

    customRender(<Search />);

    expect(screen.getByText("⌘")).toBeInTheDocument();
    expect(screen.getByText("K")).toBeInTheDocument();
  });

  it("renders the non-macOS keyboard shortcut", () => {
    mockUseOs.mockReturnValue("windows");

    customRender(<Search />);

    expect(screen.getByText("Ctrl")).toBeInTheDocument();
    expect(screen.getByText("K")).toBeInTheDocument();
  });

  it("opens the spotlight when the search button is clicked", async () => {
    const openSpy = vitest
      .spyOn(spotlightApi, "open")
      .mockImplementation(() => undefined);

    mockUseOs.mockReturnValue("macos");

    customRender(<Search />);

    await userEvent.click(screen.getByRole("button", { name: "Search" }));

    expect(openSpy).toHaveBeenCalledTimes(1);

    openSpy.mockRestore();
  });
});
