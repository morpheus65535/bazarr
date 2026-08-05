import { fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useLanguageProfiles, useLanguages } from "@/apis/hooks/languages";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsLanguagesView from "./index";

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

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;
const mockedUseLanguages = useLanguages as Mock;
const mockedUseLanguageProfiles = useLanguageProfiles as Mock;

const baseSettings = {
  general: {
    theme: "auto",
    instance_name: "Bazarr",
    single_language: false,
    parse_embedded_audio_track: false,
    default_und_audio_lang: "",
    default_und_embedded_subtitles_lang: "",
    serie_tag_enabled: false,
    movie_tag_enabled: false,
    remove_profile_tags: [],
    serie_default_enabled: false,
    movie_default_enabled: false,
    serie_default_profile: null,
    movie_default_profile: null,
    language_equals: [] as string[],
  },
  languages: {
    enabled: [] as Language.Info[],
    profiles: [] as Language.Profile[],
  },
};

const baseLanguages: Language.Server[] = [
  { code2: "en", code3: "eng", name: "English", enabled: true },
  { code2: "fr", code3: "fre", name: "French", enabled: true },
  { code2: "de", code3: "deu", name: "German", enabled: false },
];

const baseProfiles: Language.Profile[] = [
  {
    profileId: 1,
    name: "My Profile",
    tag: "mytag",
    items: [
      {
        id: 1,
        language: "en",
        audioExclude: "False",
        audioOnlyInclude: "False",
        hi: "False",
        forced: "False",
      },
      {
        id: 2,
        language: "fr",
        audioExclude: "False",
        audioOnlyInclude: "False",
        hi: "True",
        forced: "False",
      },
    ],
    cutoff: 1,
    mustContain: [],
    mustNotContain: [],
    originalFormat: false,
  },
];

const setupMocks = (
  overrides?: {
    settings?: Partial<typeof baseSettings>;
    languages?: Language.Server[];
    profiles?: Language.Profile[];
  },
  mutate?: ReturnType<typeof vitest.fn>,
) => {
  const languageOverrides = overrides?.settings?.languages;
  const settings = {
    ...baseSettings,
    ...overrides?.settings,
    general: {
      ...baseSettings.general,
      ...overrides?.settings?.general,
    },
    languages: {
      ...baseSettings.languages,
      ...languageOverrides,
      enabled:
        languageOverrides?.enabled !== undefined
          ? languageOverrides.enabled
          : (overrides?.languages ?? baseSettings.languages.enabled),
      profiles:
        languageOverrides?.profiles !== undefined
          ? languageOverrides.profiles
          : (overrides?.profiles ?? baseSettings.languages.profiles),
    },
  };

  mockedUseSystemSettings.mockReturnValue({
    data: settings as unknown as Settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: mutate ?? vitest.fn(),
    isPending: false,
  });
  mockedUseLanguages.mockReturnValue({
    data: overrides?.languages ?? [],
    isLoading: false,
    isRefetching: false,
  });
  mockedUseLanguageProfiles.mockReturnValue({
    data: overrides?.profiles ?? [],
    isLoading: false,
    isRefetching: false,
  });
};

const renderPage = (
  overrides?: {
    settings?: Partial<typeof baseSettings>;
    languages?: Language.Server[];
    profiles?: Language.Profile[];
  },
  mutate?: ReturnType<typeof vitest.fn>,
) => {
  setupMocks(overrides, mutate);
  return customRender(<SettingsLanguagesView />);
};

describe("SettingsLanguagesView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render all language sections", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Subtitles Language" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Language Equals" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Embedded Tracks Language" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Languages Profile" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Tag-Based Automatic Language Profile Selection Settings",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Default Language Profiles For Newly Added Shows",
      }),
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

  it("should expand default profile selectors when enabled", () => {
    renderPage({
      settings: {
        general: {
          ...baseSettings.general,
          serie_default_enabled: true,
          movie_default_enabled: true,
        },
      },
      languages: baseLanguages,
    });

    const profileSelectors = screen.getAllByRole("combobox", {
      name: "Profile",
    });

    expect(profileSelectors).toHaveLength(2);
  });

  it("should disable adding profiles when no languages are enabled", () => {
    renderPage();

    const addButton = screen.getByRole("button", {
      name: "No Enabled Languages",
    });

    expect(addButton).toBeDisabled();
  });

  it("should render existing language profiles and their language badges", () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    expect(screen.getByText("My Profile")).toBeInTheDocument();
    expect(screen.getByText("en")).toBeInTheDocument();
    expect(screen.getByText("fr:HI")).toBeInTheDocument();
  });

  it("should remove a language profile from the table", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    const removeButton = screen.getByRole("button", { name: "Remove" });

    await userEvent.click(removeButton);

    await waitFor(() =>
      expect(screen.queryByText("My Profile")).not.toBeInTheDocument(),
    );
  });

  it("should add a new language profile from the modal", async () => {
    renderPage({
      languages: baseLanguages,
    });

    await userEvent.click(
      screen.getByRole("button", { name: "Add New Profile" }),
    );

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const nameInput = modalScope.getByRole("textbox", { name: "Name" });

    fireEvent.change(nameInput, { target: { value: "New Profile" } });

    await userEvent.click(
      modalScope.getByRole("button", { name: "Add Language" }),
    );

    await userEvent.click(modalScope.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    expect(screen.getByText("New Profile")).toBeInTheDocument();
  });

  it("should edit an existing language profile from the modal", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    const editButton = screen.getByRole("button", { name: "Edit Profile" });

    await userEvent.click(editButton);

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const nameInput = modalScope.getByRole("textbox", { name: "Name" });

    fireEvent.change(nameInput, { target: { value: "Updated Profile" } });

    await userEvent.click(modalScope.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    expect(screen.getByText("Updated Profile")).toBeInTheDocument();
    expect(screen.queryByText("My Profile")).not.toBeInTheDocument();
  });

  it("should render existing language equals", () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: ["eng@hi:fre"],
        },
      },
    });

    const hiCheckboxes = screen.getAllByRole("checkbox", { name: "HI" });
    const forcedCheckboxes = screen.getAllByRole("checkbox", {
      name: "Forced",
    });

    expect(hiCheckboxes[0]).toBeChecked();
    expect(hiCheckboxes[1]).not.toBeChecked();
    expect(forcedCheckboxes[0]).not.toBeChecked();
    expect(forcedCheckboxes[1]).not.toBeChecked();
  });

  it("should add a language equal when clicking Add Equal", async () => {
    renderPage({
      languages: baseLanguages,
    });

    await userEvent.click(screen.getByRole("button", { name: "Add Equal" }));

    const hiCheckboxes = screen.getAllByRole("checkbox", { name: "HI" });
    const forcedCheckboxes = screen.getAllByRole("checkbox", {
      name: "Forced",
    });

    expect(hiCheckboxes).toHaveLength(2);
    expect(forcedCheckboxes).toHaveLength(2);
  });

  it("should toggle HI and Forced checkboxes in language equals", async () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: ["eng:fre"],
        },
      },
    });

    const hiCheckboxes = screen.getAllByRole("checkbox", { name: "HI" });

    expect(hiCheckboxes[0]).not.toBeChecked();

    await userEvent.click(hiCheckboxes[0]);

    const hiCheckboxesAfterFirst = screen.getAllByRole("checkbox", {
      name: "HI",
    });
    const forcedCheckboxesAfterFirst = screen.getAllByRole("checkbox", {
      name: "Forced",
    });

    expect(hiCheckboxesAfterFirst[0]).toBeChecked();
    expect(forcedCheckboxesAfterFirst[0]).not.toBeChecked();

    await userEvent.click(forcedCheckboxesAfterFirst[0]);

    const hiCheckboxesAfterSecond = screen.getAllByRole("checkbox", {
      name: "HI",
    });
    const forcedCheckboxesAfterSecond = screen.getAllByRole("checkbox", {
      name: "Forced",
    });

    expect(forcedCheckboxesAfterSecond[0]).toBeChecked();
    expect(hiCheckboxesAfterSecond[0]).not.toBeChecked();
  });

  it("should remove a language equal", async () => {
    renderPage({
      languages: baseLanguages,
      settings: {
        general: {
          ...baseSettings.general,
          language_equals: ["eng:fre"],
        },
      },
    });

    const removeButton = screen.getByRole("button", { name: "Remove" });

    await userEvent.click(removeButton);

    await waitFor(() => {
      expect(screen.queryAllByRole("checkbox", { name: "HI" })).toHaveLength(0);
    });
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

  it("should select a default language profile for series", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
      settings: {
        general: {
          ...baseSettings.general,
          serie_default_enabled: true,
        },
      },
    });

    const profile = screen.getByRole("combobox", { name: "Profile" });

    await userEvent.click(profile);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "My Profile",
    });

    fireEvent.click(option);

    expect(profile).toHaveValue("My Profile");
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

  it("should fall back to API profiles for the default profile selector", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
      settings: {
        ...baseSettings,
        languages: {
          enabled: null as unknown as Language.Info[],
          profiles: null as unknown as Language.Profile[],
        },
        general: {
          ...baseSettings.general,
          serie_default_enabled: true,
        },
      },
    });

    const profile = screen.getByRole("combobox", { name: "Profile" });

    await userEvent.click(profile);

    expect(
      screen.getByRole("option", { hidden: true, name: "My Profile" }),
    ).toBeInTheDocument();
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

  it("should save the default profile selector with the onSubmit fallback", async () => {
    const mutate = vitest.fn();

    renderPage(
      {
        languages: baseLanguages,
        profiles: baseProfiles,
        settings: {
          ...baseSettings,
          general: {
            ...baseSettings.general,
            serie_default_enabled: true,
          },
        },
      },
      mutate,
    );

    const profile = screen.getByRole("combobox", { name: "Profile" });

    await userEvent.click(profile);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "My Profile",
    });

    fireEvent.click(option);

    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;

    expect(submitted["settings-general-serie_default_profile"]).toBe(1);
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

  it("should sanitize remove profile tags when saving", async () => {
    const mutate = vitest.fn();

    renderPage(
      {
        languages: baseLanguages,
        settings: {
          ...baseSettings,
          general: {
            ...baseSettings.general,
            remove_profile_tags: [],
          },
        },
      },
      mutate,
    );

    const chipInput = screen.getByRole("combobox", {
      name: "Remove Profile Tags",
    });

    await userEvent.type(chipInput, "Bad_Tag!123");
    await userEvent.keyboard("{Enter}");

    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;

    expect(submitted["settings-general-remove_profile_tags"]).toEqual([
      "bad_tag123",
    ]);
  });
});
