import { ReactElement } from "react";
import type { UseFormReturnType } from "@mantine/form";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, vitest } from "vitest";
import api from "@/apis/raw";
import { FormContext, FormValues } from "@/pages/Settings/utilities/FormValues";
import { SettingsProvider } from "@/pages/Settings/utilities/SettingsProvider";
import { AllProviders } from "@/providers";
import { ProviderTestButton, URLTestButton } from "./index";

const sonarrSettings = {
  sonarr: {
    ip: "127.0.0.1",
    port: 8989,
    base_url: "sonarr",
    apikey: "abc123",
    ssl: false,
  },
} as unknown as Settings;

const providerSettings = {
  opensubtitlescom: {
    endpoint: "http://api.opensubtitles.com",
  },
} as unknown as Settings;

function createForm(): UseFormReturnType<FormValues> {
  return {
    values: { settings: {}, hooks: {} },
  } as unknown as UseFormReturnType<FormValues>;
}

function renderWithSettings(ui: ReactElement, settings: Settings) {
  const form = createForm();
  return render(
    <AllProviders>
      <SettingsProvider value={settings}>
        <FormContext.Provider value={form}>{ui}</FormContext.Provider>
      </SettingsProvider>
    </AllProviders>,
  );
}

describe("Settings test buttons", () => {
  it("URLTestButton tests the URL and shows the version", async () => {
    const urlTest = vitest
      .fn()
      .mockResolvedValue({ status: true, version: "3.0", code: 200 });
    vi.spyOn(api.utils, "urlTest").mockImplementation(urlTest);

    renderWithSettings(
      <URLTestButton category="sonarr"></URLTestButton>,
      sonarrSettings,
    );

    const button = screen.getByRole("button", { name: "Test" });
    await userEvent.click(button);

    expect(urlTest).toHaveBeenCalledWith("http", "127.0.0.1:8989/sonarr/", {
      apikey: "abc123",
    });
    await screen.findByRole("button", { name: "Version: 3.0" });
  });

  it("ProviderTestButton tests the provider URL and shows the version", async () => {
    const providerUrlTest = vitest
      .fn()
      .mockResolvedValue({ status: true, version: "1.0", code: 200 });
    vi.spyOn(api.utils, "providerUrlTest").mockImplementation(providerUrlTest);

    renderWithSettings(
      <ProviderTestButton category="opensubtitlescom"></ProviderTestButton>,
      providerSettings,
    );

    const button = screen.getByRole("button", { name: "Test Connection" });
    await userEvent.click(button);

    expect(providerUrlTest).toHaveBeenCalledWith(
      "http",
      "api.opensubtitles.com/",
    );
    await screen.findByRole("button", { name: "1.0" });
  });

  it("URLTestButton shows an error when the test fails", async () => {
    const urlTest = vitest
      .fn()
      .mockResolvedValue({
        status: false,
        error: "Connection failed",
        code: 500,
      });
    vi.spyOn(api.utils, "urlTest").mockImplementation(urlTest);

    renderWithSettings(
      <URLTestButton category="sonarr"></URLTestButton>,
      sonarrSettings,
    );

    const button = screen.getByRole("button", { name: "Test" });
    await userEvent.click(button);

    await screen.findByRole("button", { name: "Connection failed" });
  });

  it("URLTestButton does nothing when required fields are missing", async () => {
    const urlTest = vitest
      .fn()
      .mockResolvedValue({ status: true, version: "3.0" });
    vi.spyOn(api.utils, "urlTest").mockImplementation(urlTest);

    renderWithSettings(
      <URLTestButton category="sonarr"></URLTestButton>,
      {} as unknown as Settings,
    );

    const button = screen.getByRole("button", { name: "Test" });
    await userEvent.click(button);

    expect(urlTest).not.toHaveBeenCalled();
    expect(button).toHaveTextContent("Test");
  });

  it("ProviderTestButton shows a 404-specific message", async () => {
    const providerUrlTest = vitest
      .fn()
      .mockResolvedValue({ status: false, code: 404 });
    vi.spyOn(api.utils, "providerUrlTest").mockImplementation(providerUrlTest);

    renderWithSettings(
      <ProviderTestButton category="opensubtitlescom"></ProviderTestButton>,
      providerSettings,
    );

    const button = screen.getByRole("button", { name: "Test Connection" });
    await userEvent.click(button);

    await screen.findByRole("button", {
      name: "Connected but no version found (possibly whisper-asr?)",
    });
  });

  it("ProviderTestButton shows a generic error when the test fails", async () => {
    const providerUrlTest = vitest
      .fn()
      .mockResolvedValue({ status: false, code: 500, error: "Server error" });
    vi.spyOn(api.utils, "providerUrlTest").mockImplementation(providerUrlTest);

    renderWithSettings(
      <ProviderTestButton category="opensubtitlescom"></ProviderTestButton>,
      providerSettings,
    );

    const button = screen.getByRole("button", { name: "Test Connection" });
    await userEvent.click(button);

    await screen.findByRole("button", { name: "Server error" });
  });
});
