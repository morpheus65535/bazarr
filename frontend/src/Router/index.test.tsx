import { ReactElement } from "react";
import { createBrowserRouter } from "react-router";
import { vi } from "vitest";
import { useBadges } from "@/apis/hooks";
import { useEnabledStatus } from "@/apis/hooks/site";
import { rawRender } from "@/tests";
import { Router } from "./index";
import { CustomRouteObject } from "./type";

vi.mock("react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    createBrowserRouter: vi.fn(() => ({})),
    RouterProvider: () => null,
  };
});

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return { ...actual, useBadges: vi.fn() };
});

vi.mock("@/apis/hooks/site", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/site")>();
  return { ...actual, useEnabledStatus: vi.fn() };
});

const mockedCreateBrowserRouter = vi.mocked(createBrowserRouter);
const mockedUseBadges = vi.mocked(useBadges);
const mockedUseEnabledStatus = vi.mocked(useEnabledStatus);

const getSettingsRoutes = (): CustomRouteObject[] => {
  mockedUseBadges.mockReturnValue({ data: undefined } as ReturnType<
    typeof useBadges
  >);
  mockedUseEnabledStatus.mockReturnValue({ sonarr: true, radarr: true });

  rawRender(<Router />);

  const routes = mockedCreateBrowserRouter.mock.calls.at(-1)?.[0] as
    CustomRouteObject[] | undefined;
  const root = routes?.find((route) => route.path === "/");
  const settings = root?.children?.find((route) => route.path === "settings");

  if (!settings?.children) {
    throw new Error("Settings routes were not created");
  }

  return settings.children;
};

const getRedirectTarget = (route: CustomRouteObject): string | undefined =>
  (route.element as ReactElement<{ to?: string }> | undefined)?.props.to;

describe("Settings routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each([
    ["sonarr", "/settings/library/sonarr"],
    ["radarr", "/settings/library/radarr"],
    ["plex", "/settings/integrations/plex"],
    ["jellyfin", "/settings/integrations/jellyfin"],
  ])("redirects the legacy %s URL", (path, target) => {
    const route = getSettingsRoutes().find((item) => item.path === path);

    expect(route?.hidden).toBe(true);
    expect(route && getRedirectTarget(route)).toBe(target);
  });

  it("redirects integration and grouped settings indexes to their first tabs", () => {
    const routes = getSettingsRoutes();

    for (const [path, target] of [
      ["library", "sonarr"],
      ["integrations", "plex"],
      ["languages", "general"],
      ["providers", "subtitles"],
      ["subtitles", "files"],
      ["application", "general"],
    ]) {
      const group = routes.find((route) => route.path === path);
      const index = group?.children?.find((route) => route.index);
      expect(index && getRedirectTarget(index)).toBe(target);
    }
  });

  it.each([
    ["sonarr", "/settings/library/sonarr"],
    ["radarr", "/settings/library/radarr"],
  ])("redirects the legacy integrations/%s URL", (path, target) => {
    const integrations = getSettingsRoutes().find(
      (item) => item.path === "integrations",
    );
    const route = (
      integrations?.children as CustomRouteObject[] | undefined
    )?.find((item) => item.path === path);

    expect(route?.hidden).toBe(true);
    expect(route?.name).toBeUndefined();
    expect(route && getRedirectTarget(route)).toBe(target);
  });

  it.each([
    ["general", "/settings/subtitles/files"],
    ["translation", "/settings/providers/translation"],
  ])("redirects the legacy subtitles/%s URL", (path, target) => {
    const subtitles = getSettingsRoutes().find(
      (item) => item.path === "subtitles",
    );
    const route = (
      subtitles?.children as CustomRouteObject[] | undefined
    )?.find((item) => item.path === path);

    expect(route?.hidden).toBe(true);
    expect(route?.name).toBeUndefined();
    expect(route && getRedirectTarget(route)).toBe(target);
  });
});
