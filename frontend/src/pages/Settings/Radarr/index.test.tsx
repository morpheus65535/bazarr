import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import api from "@/apis/raw";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsRadarrView from "./index";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;

const baseSettings = {
  general: {
    theme: "auto",
    instance_name: "Bazarr",
    use_radarr: true,
    path_mappings_movie: [],
    minimum_score_movie: 0,
  },
  radarr: {
    ip: "127.0.0.1",
    port: 7878,
    base_url: "/radarr",
    apikey: "radarr-api-key",
    ssl: false,
    http_timeout: 60,
    movies_sync_on_live: false,
    excluded_tags: [],
    only_monitored: false,
    defer_search_signalr: false,
  },
} as unknown as Settings;

function setupMocks(enabled: boolean) {
  mockedUseSystemSettings.mockReturnValue({
    data: {
      ...baseSettings,
      general: {
        ...baseSettings.general,
        use_radarr: enabled,
      },
    },
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vitest.fn(),
    isPending: false,
  });
}

function renderPage(enabled: boolean) {
  setupMocks(enabled);
  return customRender(<SettingsRadarrView />);
}

describe("SettingsRadarrView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render radarr sections when enabled", () => {
    renderPage(true);

    expect(screen.getByRole("heading", { name: "Host" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Options" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Path Mappings" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Test" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add" })).toBeInTheDocument();
  });

  it("should hide connection options when radarr is disabled", () => {
    renderPage(false);

    expect(
      screen.queryByRole("heading", { name: "Host" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Test" }),
    ).not.toBeInTheDocument();
  });

  it("should strip leading slash from base URL on load", () => {
    renderPage(true);

    expect(screen.getByRole("textbox", { name: "Base URL" })).toHaveValue(
      "radarr",
    );
  });

  it("should call the connection test API when clicking test", async () => {
    const urlTestSpy = vi
      .spyOn(api.utils, "urlTest")
      .mockResolvedValue({ status: true, version: "5", code: 200 });

    renderPage(true);

    await userEvent.click(screen.getByRole("button", { name: "Test" }));

    expect(urlTestSpy).toHaveBeenCalled();
  });

  it("should sanitize an excluded tag when adding a chip", async () => {
    renderPage(true);

    const input = screen.getByRole("combobox", { name: "Excluded Tags" });

    await userEvent.type(input, "Bad Tag!");
    await userEvent.keyboard("{Enter}");

    expect(screen.getByText("badtag")).toBeInTheDocument();
  });

  it("should submit the base URL with a leading slash", async () => {
    renderPage(true);

    const baseUrlInput = screen.getByRole("textbox", { name: "Base URL" });

    await userEvent.clear(baseUrlInput);
    await userEvent.type(baseUrlInput, "newbase");

    await userEvent.click(screen.getByRole("button", { name: /^Save/ }));

    const mutate =
      mockedUseSettingsMutation.mock.results[
        mockedUseSettingsMutation.mock.results.length - 1
      ].value.mutate;

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        "settings-radarr-base_url": "/newbase",
      }),
    );
  });
});
