import { fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import api from "@/apis/raw";
import { customRender, screen } from "@/tests";
import SettingsProvidersSubtitlesView from "./Subtitles";

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
    enabled_providers: [] as string[],
    enabled_integrations: [] as string[],
  },
};

const setupMocks = (overrides?: Partial<typeof baseSettings>) => {
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
};

const renderPage = (overrides?: Partial<typeof baseSettings>) => {
  setupMocks(overrides);
  return customRender(<SettingsProvidersSubtitlesView />);
};

describe("SettingsProvidersSubtitlesView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render the enabled providers section", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Enabled Providers" }),
    ).toBeInTheDocument();
  });

  it("should render enabled provider cards", () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_providers: ["addic7ed"],
      },
    });

    expect(screen.getByText("Addic7ed")).toBeInTheDocument();
  });

  const getEnabledProviderAddButton = () =>
    screen.getAllByRole("button", { name: "Add" })[0];

  it("should open the provider modal for an enabled provider", async () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_providers: ["addic7ed"],
      },
    });

    await userEvent.click(screen.getByRole("button", { name: /Addic7ed/i }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    expect(
      modalScope.getByRole("textbox", { name: "Username" }),
    ).toBeInTheDocument();
    expect(modalScope.getByLabelText("Password")).toBeInTheDocument();
    expect(modalScope.getByRole("switch", { name: "VIP" })).toBeInTheDocument();
  });

  it("should add a new provider from the modal", async () => {
    renderPage();

    await userEvent.click(getEnabledProviderAddButton());

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const providerSelect = modalScope.getByPlaceholderText(
      "Click to Select a Provider",
    );

    await userEvent.click(providerSelect);

    const option = screen.getByRole("option", {
      hidden: true,
      name: /Whisper/i,
    });

    fireEvent.click(option);

    expect(
      modalScope.getByRole("textbox", {
        name: "Whisper ASR Docker Endpoint",
      }),
    ).toBeInTheDocument();
    expect(
      modalScope.getByRole("button", { name: "Test Connection" }),
    ).toBeInTheDocument();

    await userEvent.click(modalScope.getByRole("button", { name: "Enable" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    expect(
      screen.getByRole("button", { name: /Whisper/i }),
    ).toBeInTheDocument();
  });

  it("should not show the Disable button when adding a new provider", async () => {
    renderPage();

    await userEvent.click(getEnabledProviderAddButton());

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    expect(
      modalScope.queryByRole("button", { name: "Disable" }),
    ).not.toBeInTheDocument();
  });

  it("should disable an existing provider from the modal", async () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_providers: ["addic7ed"],
      },
    });

    await userEvent.click(screen.getByRole("button", { name: /Addic7ed/i }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    await userEvent.click(modalScope.getByRole("button", { name: "Disable" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    expect(
      screen.queryByRole("button", { name: /Addic7ed/i }),
    ).not.toBeInTheDocument();
  });

  it("should warn when a provider's required integration is not enabled", async () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_providers: ["animetosho"],
        enabled_integrations: [],
      },
    });

    await userEvent.click(screen.getByRole("button", { name: /Anime Tosho/i }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    expect(
      modalScope.getByText(/AniDB integration required/i),
    ).toBeInTheDocument();
    expect(modalScope.getByText(/is not enabled yet/i)).toBeInTheDocument();
  });

  it("should warn when the required integration is enabled but missing credentials", async () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_providers: ["animetosho"],
        enabled_integrations: ["anidb"],
      },
    });

    await userEvent.click(screen.getByRole("button", { name: /Anime Tosho/i }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    expect(
      modalScope.getByText(/AniDB integration required/i),
    ).toBeInTheDocument();
    expect(modalScope.getByText(/missing its API Client/i)).toBeInTheDocument();
  });

  it("should confirm when the required integration is enabled and configured", async () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_providers: ["animetosho"],
        enabled_integrations: ["anidb"],
      },
      anidb: {
        api_client: "my-client",
        api_client_ver: 1,
      },
    } as unknown as Partial<typeof baseSettings>);

    await userEvent.click(screen.getByRole("button", { name: /Anime Tosho/i }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    expect(
      modalScope.getByText(/is enabled and configured/i),
    ).toBeInTheDocument();
  });

  it("should test a provider connection from the modal", async () => {
    const providerTestSpy = vi
      .spyOn(api.utils, "providerUrlTest")
      .mockResolvedValue({ status: true, version: "1", code: 200 });

    renderPage();

    await userEvent.click(getEnabledProviderAddButton());

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const providerSelect = modalScope.getByPlaceholderText(
      "Click to Select a Provider",
    );

    await userEvent.click(providerSelect);

    const option = screen.getByRole("option", {
      hidden: true,
      name: /Whisper/i,
    });

    fireEvent.click(option);

    const endpointInput = modalScope.getByRole("textbox", {
      name: "Whisper ASR Docker Endpoint",
    });

    await userEvent.type(endpointInput, "http://127.0.0.1:9000");

    await userEvent.click(
      modalScope.getByRole("button", { name: "Test Connection" }),
    );

    expect(providerTestSpy).toHaveBeenCalledWith("http", "127.0.0.1:9000/");
  });
});
