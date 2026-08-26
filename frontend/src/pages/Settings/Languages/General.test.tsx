import { fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import SettingsLanguagesGeneralView from "./General";
import { baseLanguages, baseSettings, setupMocks } from "./testing";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/languages", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/apis/hooks/languages")>();
  return {
    ...actual,
    useLanguages: vitest.fn(),
    useLanguageProfiles: vitest.fn(),
  };
});

const renderPage = (
  overrides?: Parameters<typeof setupMocks>[0],
  mutate?: ReturnType<typeof vitest.fn>,
) => {
  setupMocks(overrides, mutate);
  return customRender(<SettingsLanguagesGeneralView />);
};

describe("SettingsLanguagesGeneralView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render the general language sections", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Subtitles Language" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Embedded Tracks Language" }),
    ).toBeInTheDocument();
  });

  it("should expand the unknown audio track selector when parsing is enabled", () => {
    renderPage({
      settings: {
        general: {
          ...baseSettings.general,
          parse_embedded_audio_track: true,
        },
      },
    });

    expect(
      screen.getByRole("combobox", {
        name: /Treat unknown language audio track as/i,
      }),
    ).toBeInTheDocument();
  });

  it("should add a language in the language filter", async () => {
    renderPage({
      languages: baseLanguages,
    });

    const filter = screen.getAllByRole("combobox")[0];

    await userEvent.click(filter);

    const option = screen.getByRole("option", { hidden: true, name: "German" });

    fireEvent.click(option);

    expect(screen.getAllByText("German").length).toBeGreaterThanOrEqual(1);
  });

  it("should fall back to API enabled languages when the language setting is absent", () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        ...baseSettings,
        languages: {
          enabled: null as unknown as Language.Info[],
          profiles: [],
        },
      },
    });

    expect(screen.getAllByText("English").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("French").length).toBeGreaterThanOrEqual(1);
  });

  it("should save the language filter with mapped language codes", async () => {
    const mutate = vitest.fn();

    renderPage(
      {
        languages: baseLanguages,
      },
      mutate,
    );

    const filter = screen.getAllByRole("combobox")[0];

    await userEvent.click(filter);

    const option = screen.getByRole("option", { hidden: true, name: "German" });

    fireEvent.click(option);

    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;

    expect(submitted["languages-enabled"]).toContain("de");
  });

  it("should save embedded track language selectors with the onSubmit fallback", async () => {
    const mutate = vitest.fn();

    renderPage(
      {
        languages: baseLanguages,
        settings: {
          ...baseSettings,
          general: {
            ...baseSettings.general,
            parse_embedded_audio_track: true,
          },
        },
      },
      mutate,
    );

    const audioSelect = screen.getByRole("combobox", {
      name: /Treat unknown language audio track as/i,
    });

    await userEvent.click(audioSelect);

    const audioOptions = screen.getAllByRole("option", {
      hidden: true,
      name: "English",
    });

    fireEvent.click(audioOptions[0]);

    const embeddedSelect = screen.getByRole("combobox", {
      name: /Treat unknown language embedded subtitles track as/i,
    });

    await userEvent.click(embeddedSelect);

    const embeddedOptions = screen.getAllByRole("option", {
      hidden: true,
      name: "French",
    });

    fireEvent.click(embeddedOptions[embeddedOptions.length - 1]);

    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;

    expect(submitted["settings-general-default_und_audio_lang"]).toBe("en");
    expect(
      submitted["settings-general-default_und_embedded_subtitles_lang"],
    ).toBe("fr");
  });
});
