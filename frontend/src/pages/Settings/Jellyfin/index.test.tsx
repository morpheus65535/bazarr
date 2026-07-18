import { fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import {
  useJellyfinLibrariesQuery,
  useJellyfinTestConnectionMutation,
} from "@/apis/hooks/jellyfin";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsJellyfinView from "./index";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/jellyfin", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/jellyfin")>();
  return {
    ...actual,
    useJellyfinLibrariesQuery: vitest.fn(),
    useJellyfinTestConnectionMutation: vitest.fn(),
  };
});

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;
const mockedUseJellyfinLibrariesQuery = useJellyfinLibrariesQuery as Mock;
const mockedUseJellyfinTestConnectionMutation =
  useJellyfinTestConnectionMutation as Mock;

const mockMutate = vitest.fn();

const baseSettings = {
  general: {
    theme: "auto",
    instance_name: "Bazarr",
    use_jellyfin: true,
  },
  jellyfin: {
    url: "http://localhost:8096",
    apikey: "jellyfin-api-key",
    refresh_method: "immediate",
    movie_library: [] as string[],
    movie_library_ids: [] as string[],
    series_library: [] as string[],
    series_library_ids: [] as string[],
    update_movie_library: false,
    update_series_library: false,
  },
};

function setupMocks(overrides?: Partial<typeof baseSettings>) {
  mockedUseSystemSettings.mockReturnValue({
    data: {
      ...baseSettings,
      ...overrides,
    } as unknown as Settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vitest.fn(),
    isPending: false,
  });
  mockedUseJellyfinLibrariesQuery.mockReturnValue({
    data: [],
    isLoading: false,
    error: null,
  });
  mockedUseJellyfinTestConnectionMutation.mockReturnValue({
    mutate: mockMutate,
    isPending: false,
  });
}

function renderPage(
  overrides?: Partial<typeof baseSettings>,
  libraryQuery?: ReturnType<typeof mockedUseJellyfinLibrariesQuery>,
) {
  setupMocks(overrides);
  if (libraryQuery) {
    mockedUseJellyfinLibrariesQuery.mockReturnValue(libraryQuery);
  }
  return customRender(<SettingsJellyfinView />);
}

describe("SettingsJellyfinView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  beforeAll(() => {
    Element.prototype.scrollIntoView = vitest.fn();
  });

  it("should render jellyfin sections when enabled", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Connection" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Movie Library" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Series Library" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Test" })).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", {
        name: "How to notify Jellyfin after subtitle changes",
      }),
    ).toBeInTheDocument();
  });

  it("should hide connection options when jellyfin is disabled", () => {
    renderPage({
      general: { ...baseSettings.general, use_jellyfin: false },
    });

    expect(
      screen.queryByRole("heading", { name: "Connection" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Test" }),
    ).not.toBeInTheDocument();
  });

  it("should prompt to configure URL and API key before discovering libraries", () => {
    renderPage({
      jellyfin: { ...baseSettings.jellyfin, url: "", apikey: "" },
    });

    const alerts = screen.getAllByText(
      /Configure Jellyfin URL and API Key above to discover libraries/i,
    );

    expect(alerts).toHaveLength(2);
  });

  it("should warn when testing connection without URL or API key", async () => {
    renderPage({
      jellyfin: { ...baseSettings.jellyfin, url: "", apikey: "" },
    });

    const testButton = screen.getByRole("button", { name: "Test" });

    await userEvent.click(testButton);

    expect(
      screen.getByRole("button", { name: "URL and API Key required" }),
    ).toBeInTheDocument();
    expect(mockMutate).not.toHaveBeenCalled();
  });

  it("should update the test button on a successful connection", async () => {
    mockMutate.mockImplementation((_, options) => {
      options.onSuccess({
        success: true,
        serverName: "Jellyfin",
        version: "10.8",
      });
    });

    renderPage();

    await userEvent.click(screen.getByRole("button", { name: "Test" }));

    expect(
      screen.getByRole("button", { name: "Jellyfin (v10.8)" }),
    ).toBeInTheDocument();
  });

  it("should update the test button on a failed connection", async () => {
    mockMutate.mockImplementation((_, options) => {
      options.onSuccess({
        success: false,
        error: "Connection failed",
      });
    });

    renderPage();

    await userEvent.click(screen.getByRole("button", { name: "Test" }));

    expect(
      screen.getByRole("button", { name: "Connection failed" }),
    ).toBeInTheDocument();
  });

  it("should change the refresh method", async () => {
    renderPage();

    const refreshMethodSelect = screen.getByRole("combobox", {
      name: "How to notify Jellyfin after subtitle changes",
    });

    await userEvent.click(refreshMethodSelect);

    const option = screen.getByRole("option", { hidden: true, name: /Async/i });

    await userEvent.click(option);

    expect(refreshMethodSelect).toHaveValue("Async");
  });

  it("should show a loading alert while fetching libraries", () => {
    renderPage(undefined, {
      data: undefined,
      isLoading: true,
      error: null,
    });

    expect(
      screen.getAllByText("Fetching libraries from Jellyfin...").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should show an error alert when library discovery fails", () => {
    renderPage(undefined, {
      data: undefined,
      isLoading: false,
      error: new Error("Failed"),
    });

    expect(
      screen.getAllByText("Failed to load libraries from Jellyfin.").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should show a no libraries alert when none are found", () => {
    renderPage(undefined, {
      data: [],
      isLoading: false,
      error: null,
    });

    expect(
      screen.getAllByText("No movie libraries found.").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should mark stale libraries as unavailable", () => {
    renderPage(
      {
        jellyfin: {
          ...baseSettings.jellyfin,
          movie_library: ["Old Library"],
        },
      },
      {
        data: [{ id: "1", name: "Movies", type: "movies" }],
        isLoading: false,
        error: null,
      },
    );

    expect(
      screen.getAllByText("Old Library (unavailable)").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should select a movie library and update its id", async () => {
    renderPage(undefined, {
      data: [{ id: "1", name: "Movies", type: "movies" }],
      isLoading: false,
      error: null,
    });

    const select = screen.getAllByRole("combobox")[1];

    await userEvent.click(select);

    const option = screen.getByRole("option", { hidden: true, name: "Movies" });

    fireEvent.click(option);

    expect(screen.getAllByText("Movies").length).toBeGreaterThanOrEqual(1);
  });

  it("should show an error when the connection test fails", async () => {
    mockMutate.mockImplementation((_, options) => {
      options.onError(new Error("Network error"));
    });

    renderPage();

    await userEvent.click(screen.getByRole("button", { name: "Test" }));

    expect(
      screen.getByRole("button", { name: "Connection failed" }),
    ).toBeInTheDocument();
  });

  it("should normalize a single string movie library value", () => {
    renderPage(
      {
        jellyfin: {
          ...baseSettings.jellyfin,
          movie_library: "Movies" as unknown as string[],
        },
      },
      {
        data: [{ id: "1", name: "Movies", type: "movies" }],
        isLoading: false,
        error: null,
      },
    );

    expect(screen.getAllByText("Movies").length).toBeGreaterThanOrEqual(1);
  });
});
