import { useNavigate } from "react-router";
import { useSpotlight } from "@mantine/spotlight";
import { describe, expect, it, vitest } from "vitest";
import { useServerSearch } from "@/apis/hooks";
import { CustomRouteObject } from "@/Router/type";
import { useRouteItems } from "@/Router/useRouteItems";
import { customRender } from "@/tests";
import { useDebouncedValue } from "@/utilities";
import AppSpotlight from "./AppSpotlight";
import { buildNavActions } from "./buildNavActions";

vitest.mock("react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router")>();
  return { ...actual, useNavigate: vitest.fn() };
});

vitest.mock("@/Router/useRouteItems", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/Router/useRouteItems")>();
  return { ...actual, useRouteItems: vitest.fn() };
});

vitest.mock("@mantine/spotlight", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@mantine/spotlight")>();
  return { ...actual, useSpotlight: vitest.fn() };
});

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return { ...actual, useServerSearch: vitest.fn() };
});

vitest.mock("@/utilities", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/utilities")>();
  return { ...actual, useDebouncedValue: vitest.fn((v) => v) };
});

const mockUseNavigate = vitest.mocked(useNavigate);
const mockUseRouteItems = vitest.mocked(useRouteItems);
const mockUseSpotlight = vitest.mocked(useSpotlight);
const mockUseServerSearch = vitest.mocked(useServerSearch);
const mockUseDebouncedValue = vitest.mocked(useDebouncedValue);

describe("AppSpotlight", () => {
  it("renders and fetches search results when the query is long enough", () => {
    const navigate = vitest.fn();
    mockUseNavigate.mockReturnValue(navigate);
    mockUseRouteItems.mockReturnValue([
      { path: "/settings", name: "Settings", element: null, icon: undefined },
    ] as CustomRouteObject[]);
    mockUseSpotlight.mockReturnValue({ query: "ab" } as ReturnType<
      typeof useSpotlight
    >);
    mockUseServerSearch.mockReturnValue({
      data: undefined,
    } as unknown as ReturnType<typeof useServerSearch>);
    mockUseDebouncedValue.mockReturnValue("ab");

    customRender(<AppSpotlight />);

    expect(mockUseServerSearch).toHaveBeenCalledWith("ab", true);
  });

  it("renders with empty query and no search results", () => {
    const navigate = vitest.fn();
    mockUseNavigate.mockReturnValue(navigate);
    mockUseRouteItems.mockReturnValue([] as CustomRouteObject[]);
    mockUseSpotlight.mockReturnValue({ query: "" } as ReturnType<
      typeof useSpotlight
    >);
    mockUseServerSearch.mockReturnValue({ data: [] } as unknown as ReturnType<
      typeof useServerSearch
    >);
    mockUseDebouncedValue.mockReturnValue("");

    customRender(<AppSpotlight />);

    expect(mockUseServerSearch).toHaveBeenCalledWith("", false);
  });

  it("indexes hidden settings tab pages but skips redirects and disabled sections", () => {
    const navigate = vitest.fn();
    const routes = [
      {
        path: "settings",
        name: "Settings",
        children: [
          {
            path: "integrations",
            name: "Integrations",
            element: () => null,
            children: [
              { index: true, element: null },
              {
                path: "sonarr",
                name: "Sonarr",
                hidden: true,
                element: () => null,
              },
              { path: "general", hidden: true, element: () => null },
            ],
          },
        ],
      },
      { path: "series", name: "Series", hidden: true, element: () => null },
    ] as unknown as CustomRouteObject[];

    const actions = buildNavActions(routes, navigate);
    const ids = actions.map((a) => a.id);

    expect(ids).toContain("/settings/integrations");
    expect(ids).toContain("/settings/integrations/sonarr");
    expect(ids).not.toContain("/settings/integrations/general");
    expect(ids).not.toContain("/series");
  });

  it("renders search actions for series and movies", () => {
    const navigate = vitest.fn();
    mockUseNavigate.mockReturnValue(navigate);
    mockUseRouteItems.mockReturnValue([] as CustomRouteObject[]);
    mockUseSpotlight.mockReturnValue({ query: "ab" } as ReturnType<
      typeof useSpotlight
    >);
    mockUseServerSearch.mockReturnValue({
      data: [
        { sonarrSeriesId: 1, title: "Series", year: "2020", poster: "" },
        { radarrId: 2, title: "Movie", year: "2021", poster: "" },
      ],
    } as unknown as ReturnType<typeof useServerSearch>);
    mockUseDebouncedValue.mockReturnValue("ab");

    customRender(<AppSpotlight />);

    expect(mockUseServerSearch).toHaveBeenCalledWith("ab", true);
  });
});
