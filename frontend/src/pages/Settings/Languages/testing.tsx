import { within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vitest } from "vitest";
import { useLanguageProfiles, useLanguages } from "@/apis/hooks/languages";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { screen } from "@/tests";

export const mockedUseSystemSettings = useSystemSettings as Mock;
export const mockedUseSettingsMutation = useSettingsMutation as Mock;
export const mockedUseLanguages = useLanguages as Mock;
export const mockedUseLanguageProfiles = useLanguageProfiles as Mock;

export const baseSettings = {
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

export const baseLanguages: Language.Server[] = [
  { code2: "en", code3: "eng", name: "English", enabled: true },
  { code2: "fr", code3: "fre", name: "French", enabled: true },
  { code2: "de", code3: "deu", name: "German", enabled: false },
];

export const presetLanguages: Language.Server[] = [
  ...baseLanguages,
  { code2: "ea", code3: "spl", name: "Spanish (Latino)", enabled: false },
  { code2: "es", code3: "spa", name: "Spanish", enabled: true },
];

export const baseProfiles: Language.Profile[] = [
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

export const setupMocks = (
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

export const chooseMappingOption = async (
  combobox: HTMLElement,
  name: string,
  code3: string,
) => {
  await userEvent.click(combobox);

  const listboxId = combobox.getAttribute("aria-controls");
  const listbox = screen
    .getAllByRole("listbox", { hidden: true })
    .find((element) => element.getAttribute("id") === listboxId);
  const option = listbox
    ? within(listbox)
        .getAllByRole("option", { hidden: true, name })
        .find((element) => element.getAttribute("value") === code3)
    : undefined;

  if (!option) {
    throw new Error(`Cannot find mapping option ${name} (${code3})`);
  }

  await userEvent.click(option);
};
