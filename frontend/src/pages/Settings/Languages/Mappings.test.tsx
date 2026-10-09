import { waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import SettingsLanguageMappingsView from "./Mappings";
import {
  baseLanguages,
  baseSettings,
  chooseMappingOption,
  presetLanguages,
  setupMocks,
} from "./testing";

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
  return customRender(<SettingsLanguageMappingsView />);
};

describe("SettingsLanguageMappingsView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render the mappings section", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Language Mappings" }),
    ).toBeInTheDocument();
  });

  it("should hint when no languages are enabled", () => {
    renderPage();

    expect(
      screen.getByText(/Mappings need at least one enabled language/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Enable languages in the General tab"),
    ).toBeInTheDocument();
  });

  it("should onboard users when no language mappings exist", async () => {
    renderPage({ languages: baseLanguages });

    expect(
      screen.getByText("Accept another language label"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Use a mapping when a provider or embedded track reports an acceptable subtitle differently/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create Mapping" }),
    ).toBeEnabled();

    await userEvent.click(
      screen.getByRole("button", { name: "How language mappings work" }),
    );
    expect(screen.getByText("Are mappings bidirectional?")).toBeInTheDocument();
    expect(
      screen.getByText("Does this translate subtitles?"),
    ).toBeInTheDocument();
  });

  it("should render an existing mapping as a directional card", () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: ["eng@hi:fre"],
        },
      },
    });

    expect(screen.getByText("Provider or track")).toBeInTheDocument();
    expect(screen.getByText("Canonical target")).toBeInTheDocument();
    expect(screen.getByText("Hearing impaired")).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Edit mapping English to French",
      }),
    ).toBeInTheDocument();
  });

  it("should create a guided mapping and save the existing backend format", async () => {
    const mutate = vitest.fn();
    renderPage({ languages: baseLanguages }, mutate);

    await userEvent.click(
      screen.getByRole("button", { name: "Create Mapping" }),
    );

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);
    const sourceSelector = modalScope.getByRole("combobox", {
      name: "Provider or track language",
    });

    expect(sourceSelector).toBeDisabled();

    await chooseMappingOption(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
      "French",
      "fre",
    );
    await chooseMappingOption(sourceSelector, "English", "eng");

    expect(
      modalScope.getByText(/Standard, Hearing impaired, and Forced types/i),
    ).toBeInTheDocument();
    await userEvent.click(
      modalScope.getByRole("button", { name: "Add mapping" }),
    );

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Edit alias English to French" }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /^Save/ }));

    expect(mutate).toHaveBeenCalledWith(
      {
        "settings-general-language_equals": [
          "eng:fre",
          "eng@hi:fre@hi",
          "eng@forced:fre@forced",
        ],
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("should offer disabled languages as mapping sources", async () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        languages: {
          enabled: [{ code2: "en", name: "English" }],
          profiles: [],
        },
      },
    });

    await userEvent.click(
      screen.getByRole("button", { name: "Create Mapping" }),
    );
    const modalScope = within(await screen.findByRole("dialog"));

    await chooseMappingOption(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
      "English",
      "eng",
    );
    await chooseMappingOption(
      modalScope.getByRole("combobox", {
        name: "Provider or track language",
      }),
      "German",
      "deu",
    );
    await userEvent.click(
      modalScope.getByRole("button", { name: "Add mapping" }),
    );

    expect(
      await screen.findByRole("button", {
        name: "Edit alias German to English",
      }),
    ).toBeInTheDocument();
  });

  it("should prevent a self-mapping", async () => {
    renderPage({ languages: baseLanguages });

    await userEvent.click(
      screen.getByRole("button", { name: "Create Mapping" }),
    );
    const modalScope = within(await screen.findByRole("dialog"));

    await chooseMappingOption(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
      "English",
      "eng",
    );
    await chooseMappingOption(
      modalScope.getByRole("combobox", {
        name: "Provider or track language",
      }),
      "English",
      "eng",
    );

    expect(
      modalScope.getByText(/source and target are identical/i),
    ).toBeInTheDocument();
    expect(
      modalScope.getByRole("button", { name: "Add mapping" }),
    ).toBeDisabled();
  });

  it("should preserve and display unresolved mappings", () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: ["legacy-invalid", "eng:fre"],
        },
      },
    });

    expect(screen.getByText("Unresolved mapping")).toBeInTheDocument();
    expect(screen.getByText("legacy-invalid")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Repair mapping legacy-invalid" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Edit mapping English to French" }),
    ).toBeInTheDocument();
  });

  it("should preserve unresolved values when adding another mapping", async () => {
    const mutate = vitest.fn();
    renderPage(
      {
        languages: baseLanguages,
        settings: {
          general: {
            ...baseSettings.general,
            language_equals: ["legacy-invalid"],
          },
        },
      },
      mutate,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Add language mapping" }),
    );
    const modalScope = within(await screen.findByRole("dialog"));
    await chooseMappingOption(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
      "French",
      "fre",
    );
    await chooseMappingOption(
      modalScope.getByRole("combobox", {
        name: "Provider or track language",
      }),
      "English",
      "eng",
    );
    await userEvent.click(
      modalScope.getByRole("button", { name: "Add mapping" }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^Save/ }));

    expect(mutate).toHaveBeenCalledWith(
      {
        "settings-general-language_equals": [
          "legacy-invalid",
          "eng:fre",
          "eng@hi:fre@hi",
          "eng@forced:fre@forced",
        ],
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("should group a complete type-preserving alias into one card", () => {
    renderPage({
      languages: presetLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: [
            "spl:spa",
            "spl@hi:spa@hi",
            "spl@forced:spa@forced",
          ],
        },
      },
    });

    expect(
      screen.getByRole("button", {
        name: "Edit alias Spanish (Latino) to Spanish",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Preserves Standard, HI, and Forced subtitle types."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: "Edit mapping Spanish (Latino) to Spanish",
      }),
    ).not.toBeInTheDocument();
  });

  it("should review a preset without staging it when cancelled", async () => {
    renderPage({ languages: presetLanguages });

    await userEvent.click(
      screen.getByRole("button", { name: "Spanish (Latino) → Spanish" }),
    );
    const modalScope = within(await screen.findByRole("dialog"));

    expect(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
    ).toHaveValue("Spanish");
    expect(
      modalScope.getByRole("combobox", {
        name: "Provider or track language",
      }),
    ).toHaveValue("Spanish (Latino)");
    expect(modalScope.getByText("spl:spa")).toBeInTheDocument();

    await userEvent.click(modalScope.getByRole("button", { name: "Cancel" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("should flag a partial preset for review", () => {
    renderPage({
      languages: presetLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: ["spl:spa"],
        },
      },
    });

    expect(
      screen.getByRole("button", {
        name: "Spanish (Latino) → Spanish · Needs review",
      }),
    ).toBeDisabled();
  });

  it("should create a subtitle-type fallback", async () => {
    const mutate = vitest.fn();
    renderPage({ languages: baseLanguages }, mutate);

    await userEvent.click(
      screen.getByRole("button", { name: "Create Mapping" }),
    );
    const modalScope = within(await screen.findByRole("dialog"));

    expect(
      modalScope.getByText("What do you want to accomplish?"),
    ).toBeInTheDocument();
    expect(
      modalScope.getByText(
        "Allow a specialized subtitle type to satisfy a standard request for the same language.",
      ),
    ).toBeInTheDocument();

    await userEvent.click(
      modalScope.getByRole("radio", { name: /Subtitle-type fallback/ }),
    );
    await chooseMappingOption(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
      "English",
      "eng",
    );

    expect(modalScope.getByText("eng@hi:eng")).toBeInTheDocument();
    await userEvent.click(
      modalScope.getByRole("button", { name: "Add mapping" }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^Save/ }));

    expect(mutate).toHaveBeenCalledWith(
      {
        "settings-general-language_equals": ["eng@hi:eng"],
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("should flip an alias mapping in place", async () => {
    const mutate = vitest.fn();
    renderPage(
      {
        languages: presetLanguages,
        settings: {
          general: {
            ...baseSettings.general,
            language_equals: [
              "spl:spa",
              "spl@hi:spa@hi",
              "spl@forced:spa@forced",
            ],
          },
        },
      },
      mutate,
    );

    expect(
      screen.getByRole("button", {
        name: "Edit alias Spanish (Latino) to Spanish",
      }),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: "Swap Direction" }),
    );

    expect(
      await screen.findByRole("button", {
        name: "Edit alias Spanish to Spanish (Latino)",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Swap Direction" }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /^Save/ }));

    expect(mutate).toHaveBeenCalledWith(
      {
        "settings-general-language_equals": [
          "spa:spl",
          "spa@hi:spl@hi",
          "spa@forced:spl@forced",
        ],
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("should flip an advanced mapping in place", async () => {
    const mutate = vitest.fn();
    renderPage(
      {
        languages: baseLanguages,
        settings: {
          general: {
            ...baseSettings.general,
            language_equals: ["eng@hi:fre"],
          },
        },
      },
      mutate,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Swap Direction" }),
    );

    expect(
      await screen.findByRole("button", {
        name: "Edit mapping French to English",
      }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /^Save/ }));

    expect(mutate).toHaveBeenCalledWith(
      {
        "settings-general-language_equals": ["fre:eng@hi"],
      },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("should swap target and source in the editor", async () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: [],
        },
      },
    });

    await userEvent.click(
      screen.getByRole("button", { name: "Create Mapping" }),
    );
    const modalScope = within(await screen.findByRole("dialog"));

    await chooseMappingOption(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
      "French",
      "fre",
    );
    await chooseMappingOption(
      modalScope.getByRole("combobox", {
        name: "Provider or track language",
      }),
      "English",
      "eng",
    );

    await userEvent.click(
      modalScope.getByRole("button", { name: "Swap target and source" }),
    );

    expect(
      modalScope.getByRole("combobox", { name: "Canonical language" }),
    ).toHaveValue("English");
    expect(
      modalScope.getByRole("combobox", {
        name: "Provider or track language",
      }),
    ).toHaveValue("French");
  });

  it("should confirm before removing a language mapping", async () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: ["eng:fre"],
        },
      },
    });

    await userEvent.click(
      screen.getByRole("button", {
        name: "Remove mapping English to French",
      }),
    );

    const confirmation = within(await screen.findByRole("dialog"));
    expect(
      screen.getByRole("button", { name: "Edit mapping English to French" }),
    ).toBeInTheDocument();

    await userEvent.click(confirmation.getByRole("button", { name: "Remove" }));

    await waitFor(() => {
      expect(
        screen.queryByRole("button", {
          name: "Edit mapping English to French",
        }),
      ).not.toBeInTheDocument();
    });
    expect(
      screen.getByText("Accept another language label"),
    ).toBeInTheDocument();
  });
});
