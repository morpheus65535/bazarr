import { ReactElement } from "react";
import { createBrowserRouter } from "react-router";
import { vi } from "vitest";
import { useBadges } from "@/apis/hooks";
import { useEnabledStatus } from "@/apis/hooks/site";
import BlacklistSportsView from "@/pages/Blacklist/Sports";
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
  mockedUseEnabledStatus.mockReturnValue({
    sonarr: true,
    radarr: true,
    sportarr: true,
  });

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
    ["sportarr", "/settings/library/sportarr"],
    ["plex", "/settings/integrations/plex"],
    ["jellyfin", "/settings/integrations/jellyfin"],
  ])("redirects the legacy %s URL", (path, target) => {
    const route = getSettingsRoutes().find((item) => item.path === path);

    expect(route?.hidden).toBe(true);
    expect(route && getRedirectTarget(route)).toBe(target);
  });

  it.each([
    ["sonarr", "Sonarr"],
    ["radarr", "Radarr"],
    ["sportarr", "Sportarr"],
  ])("renders the %s settings as a library tab", (path, name) => {
    const library = getSettingsRoutes().find((item) => item.path === "library");
    const route = (library?.children as CustomRouteObject[] | undefined)?.find(
      (item) => item.path === path,
    );

    expect(route?.name).toBe(name);
    expect(route?.hidden).toBe(true);
    expect(route && getRedirectTarget(route)).toBeUndefined();
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
    ["sportarr", "/settings/library/sportarr"],
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

describe("Blacklist routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const getBlacklistRoute = (status: {
    sonarr: boolean;
    radarr: boolean;
    sportarr: boolean;
  }): CustomRouteObject | undefined => {
    mockedUseBadges.mockReturnValue({ data: undefined } as ReturnType<
      typeof useBadges
    >);
    mockedUseEnabledStatus.mockReturnValue(status);

    rawRender(<Router />);

    const routes = mockedCreateBrowserRouter.mock.calls.at(-1)?.[0] as
      CustomRouteObject[] | undefined;
    const root = routes?.find((route) => route.path === "/");
    return root?.children?.find((route) => route.path === "blacklist");
  };

  it("shows the sports blacklist when only Sportarr is enabled", () => {
    const blacklist = getBlacklistRoute({
      sonarr: false,
      radarr: false,
      sportarr: true,
    });
    const sports = (
      blacklist?.children as CustomRouteObject[] | undefined
    )?.find((route) => route.path === "sports");

    expect(blacklist?.hidden).toBe(false);
    expect(sports?.name).toBe("Sports");
    expect(sports?.hidden).toBe(false);
    expect((sports?.element as ReactElement | undefined)?.type).toBe(
      BlacklistSportsView,
    );
  });

  it("hides the sports blacklist when Sportarr is disabled", () => {
    const blacklist = getBlacklistRoute({
      sonarr: true,
      radarr: false,
      sportarr: false,
    });
    const sports = (
      blacklist?.children as CustomRouteObject[] | undefined
    )?.find((route) => route.path === "sports");

    expect(blacklist?.hidden).toBe(false);
    expect(sports?.hidden).toBe(true);
  });

  it("hides the blacklist menu when no library is enabled", () => {
    const blacklist = getBlacklistRoute({
      sonarr: false,
      radarr: false,
      sportarr: false,
    });

    expect(blacklist?.hidden).toBe(true);
  });
});
