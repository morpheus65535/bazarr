import { fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import api from "@/apis/raw";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsProvidersView from "./index";

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
    anti_captcha_provider: null,
    disable_all_providers_ssl_verify: false,
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
}

function renderPage(overrides?: Partial<typeof baseSettings>) {
  setupMocks(overrides);
  return customRender(<SettingsProvidersView />);
}

describe("SettingsProvidersView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render provider sections and security option", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Enabled Providers" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Anti-Captcha Options" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Integrations" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Security" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("switch", {
        name: "Disable All Providers HTTPS Certificate Validation",
      }),
    ).toBeInTheDocument();
  });

  it("should render enabled provider and integration cards", () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_providers: ["addic7ed"],
        enabled_integrations: ["anidb"],
      },
    });

    expect(screen.getByText("Addic7ed")).toBeInTheDocument();
    expect(screen.getByText("AniDB")).toBeInTheDocument();
  });

  it("should expand anti-captcha fields when selecting a provider", async () => {
    renderPage();

    const antiCaptchaSelect = screen.getByRole("combobox", {
      name: "Choose the anti-captcha provider you want to use",
    });

    await userEvent.click(antiCaptchaSelect);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Anti-Captcha",
    });

    fireEvent.click(option);

    expect(
      screen.getByRole("textbox", { name: "Account Key" }),
    ).toBeInTheDocument();
  });

  function getEnabledProviderAddButton() {
    return screen.getAllByRole("button", { name: "Add" })[0];
  }

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
