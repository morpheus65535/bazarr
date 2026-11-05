import { fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import SettingsLanguageProfilesView from "./Profiles";
import {
  baseLanguages,
  baseProfiles,
  baseSettings,
  basicProfile,
  enhancedProfile,
  legacyProfile,
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
  return customRender(<SettingsLanguageProfilesView />);
};

const nameInput = () => screen.getByRole("textbox", { name: "Profile name" });

const chooseLanguage = async (combobox: HTMLElement, code2: string) => {
  await userEvent.click(combobox);

  const listboxId = combobox.getAttribute("aria-controls");
  const listbox = screen
    .getAllByRole("listbox", { hidden: true })
    .find((element) => element.getAttribute("id") === listboxId);
  const option = listbox
    ? within(listbox)
        .getAllByRole("option", { hidden: true })
        .find((element) => element.getAttribute("value") === code2)
    : undefined;

  if (!option) {
    throw new Error(`Cannot find language option ${code2}`);
  }

  await userEvent.click(option);
};

const saveButton = () => screen.getByRole("button", { name: /Save/ });

const submittedProfiles = (mutate: ReturnType<typeof vitest.fn>) => {
  const submitted = mutate.mock.calls[0][0] as Record<string, string>;

  return JSON.parse(submitted["languages-profiles"]) as Record<
    string,
    unknown
  >[];
};

describe("SettingsLanguageProfilesView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render the profile sections", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Languages Profile" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Tag-Based Automatic Language Profile Selection",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Default Language Profiles For Newly Added Shows",
      }),
    ).toBeInTheDocument();
  });

  it("should show default profile selectors when enabled", () => {
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

  it("should show an inline language picker when no languages are enabled", () => {
    renderPage();

    expect(
      screen.getByText(/Profiles are built from your enabled languages/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Create profile" }),
    ).not.toBeInTheDocument();
  });

  it("should reveal the profile list after enabling a language inline", async () => {
    renderPage({
      languages: baseLanguages.map((language) => ({
        ...language,
        enabled: false,
      })),
    });

    expect(
      screen.getByText(/Profiles are built from your enabled languages/i),
    ).toBeInTheDocument();

    const filter = screen.getAllByRole("combobox")[0];

    await userEvent.click(filter);

    const option = screen.getByRole("option", { hidden: true, name: "German" });

    fireEvent.click(option);

    await waitFor(() =>
      expect(
        screen.queryByText(/Profiles are built from your enabled languages/i),
      ).not.toBeInTheDocument(),
    );

    expect(
      screen.getByRole("button", { name: "Create profile" }),
    ).toBeEnabled();
  });

  it("should render existing profiles with a readable requirement summary", () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    expect(screen.getByText("My Profile")).toBeInTheDocument();
    expect(screen.getByText(/subtitles are required/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Stop searching once English subtitles are found/i),
    ).toBeInTheDocument();
  });

  it("should stage a profile deletion after confirmation", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    await userEvent.click(screen.getByRole("button", { name: "Delete" }));

    const modal = await screen.findByRole("dialog");

    await userEvent.click(
      within(modal).getByRole("button", { name: "Delete" }),
    );

    await waitFor(() =>
      expect(screen.queryByText("My Profile")).not.toBeInTheDocument(),
    );
  });

  it("should create an enhanced profile through the editor", async () => {
    renderPage({ languages: baseLanguages });

    await userEvent.click(
      screen.getByRole("button", { name: "Create profile" }),
    );

    fireEvent.change(nameInput(), { target: { value: "New Profile" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(screen.getByText("New Profile")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply changes" })).toBeNull();
  });

  it("should stage a created enhanced profile with its groups on save", async () => {
    const mutate = vitest.fn();

    renderPage({ languages: baseLanguages }, mutate);

    await userEvent.click(
      screen.getByRole("button", { name: "Create profile" }),
    );

    fireEvent.change(nameInput(), { target: { value: "New Profile" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    await userEvent.click(saveButton());

    const saved = submittedProfiles(mutate);

    expect(saved).toHaveLength(1);
    expect(saved[0]).toMatchObject({
      profileId: 1,
      name: "New Profile",
      profileType: "enhanced",
      cutoff: null,
    });
    expect(saved[0].items).toEqual({
      groups: [
        {
          id: 1,
          operator: "AND",
          items: [
            {
              id: 1,
              language: "en",
              audio_exclude: "False",
              audio_only_include: "False",
              hi: "False",
              forced: "False",
            },
          ],
        },
      ],
    });
  });

  it("should not persist a profile when applying changes", async () => {
    const mutate = vitest.fn();

    renderPage({ languages: baseLanguages }, mutate);

    await userEvent.click(
      screen.getByRole("button", { name: "Create profile" }),
    );

    fireEvent.change(nameInput(), { target: { value: "New Profile" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(mutate).not.toHaveBeenCalled();
  });

  it("should show a pending save hint after applying changes", async () => {
    renderPage({ languages: baseLanguages });

    await userEvent.click(
      screen.getByRole("button", { name: "Create profile" }),
    );

    fireEvent.change(nameInput(), { target: { value: "New Profile" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(screen.getByText(/unsaved profile changes/i)).toBeInTheDocument();
  });

  it("should edit an existing profile name", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    await userEvent.click(screen.getByRole("button", { name: "Edit" }));

    fireEvent.change(nameInput(), { target: { value: "Updated Profile" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(screen.getByText("Updated Profile")).toBeInTheDocument();
    expect(screen.queryByText("My Profile")).not.toBeInTheDocument();
  });

  it("should keep the previous profile when a dirty draft is discarded", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    await userEvent.click(screen.getByRole("button", { name: "Edit" }));

    fireEvent.change(nameInput(), { target: { value: "Changed" } });

    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

    const modal = await screen.findByRole("dialog");

    await userEvent.click(
      within(modal).getByRole("button", { name: "Discard" }),
    );

    expect(screen.getByText("My Profile")).toBeInTheDocument();
    expect(screen.queryByText("Changed")).not.toBeInTheDocument();
  });

  it("should disable the outer Save action while editing", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: baseProfiles,
    });

    await userEvent.click(screen.getByRole("button", { name: "Edit" }));

    expect(saveButton()).toBeDisabled();
  });

  it("should disable Apply until the draft changes", async () => {
    renderPage({ languages: baseLanguages });

    await userEvent.click(
      screen.getByRole("button", { name: "Create profile" }),
    );

    expect(
      screen.getByRole("button", { name: "Apply changes" }),
    ).toBeDisabled();
  });

  it("should block applying a profile without a name", async () => {
    renderPage({ languages: baseLanguages });

    await userEvent.click(
      screen.getByRole("button", { name: "Create profile" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Add language" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(
      await screen.findByText("Give this profile a name."),
    ).toBeInTheDocument();
  });

  it("should block a language repeated with the same subtitle type", async () => {
    renderPage({ languages: baseLanguages });

    await userEvent.click(
      screen.getByRole("button", { name: "Create profile" }),
    );

    fireEvent.change(nameInput(), { target: { value: "Series Rule" } });

    await userEvent.click(screen.getByRole("button", { name: "Add language" }));

    const languageSelects = screen.getAllByRole("combobox", {
      name: "Language",
    });

    await chooseLanguage(languageSelects[1], "en");

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(await screen.findByText(/cannot repeat/)).toBeInTheDocument();
  });

  it("should open an existing enhanced profile with its groups", async () => {
    renderPage({
      languages: baseLanguages,
      profiles: [enhancedProfile],
    });

    await userEvent.click(screen.getByRole("button", { name: "Edit" }));

    expect(nameInput()).toHaveValue("Enhanced Profile");
    expect(screen.getByText("Requirement 1")).toBeInTheDocument();
    expect(screen.getByText("Requirement 2")).toBeInTheDocument();
    expect(screen.getAllByText("All languages")).toHaveLength(2);
    expect(screen.getAllByText("Any language")).toHaveLength(2);
  });

  it("should save enhanced groups unchanged when another profile is removed", async () => {
    const mutate = vitest.fn();

    renderPage(
      {
        languages: baseLanguages,
        profiles: [basicProfile, enhancedProfile],
      },
      mutate,
    );

    await userEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    const modal = await screen.findByRole("dialog");

    await userEvent.click(
      within(modal).getByRole("button", { name: "Delete" }),
    );

    await userEvent.click(saveButton());

    const saved = submittedProfiles(mutate);

    expect(saved).toHaveLength(1);
    expect(saved[0]).not.toHaveProperty("groups");
    expect(saved[0]).toMatchObject({
      profileId: 2,
      profileType: "enhanced",
      cutoff: 2,
    });
    expect(saved[0].items).toEqual({
      groups: [
        {
          id: 1,
          operator: "AND",
          items: [
            {
              id: 1,
              language: "en",
              audio_exclude: "False",
              audio_only_include: "False",
              hi: "False",
              forced: "False",
            },
            {
              id: 2,
              language: "fr",
              audio_exclude: "False",
              audio_only_include: "False",
              hi: "False",
              forced: "False",
            },
          ],
        },
        {
          id: 2,
          operator: "OR",
          items: [
            {
              id: 3,
              language: "de",
              audio_exclude: "False",
              audio_only_include: "False",
              hi: "False",
              forced: "False",
            },
            {
              id: 4,
              language: "it",
              audio_exclude: "False",
              audio_only_include: "False",
              hi: "False",
              forced: "False",
            },
          ],
        },
      ],
    });
  });

  it("should keep a legacy profile flat and untyped after an edit", async () => {
    const mutate = vitest.fn();

    renderPage(
      {
        languages: baseLanguages,
        profiles: [legacyProfile],
      },
      mutate,
    );

    await userEvent.click(screen.getByRole("button", { name: "Edit" }));

    fireEvent.change(nameInput(), { target: { value: "Legacy Renamed" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    await userEvent.click(saveButton());

    const saved = submittedProfiles(mutate);

    expect(saved).toHaveLength(1);
    expect(saved[0]).not.toHaveProperty("profileType");
    expect(saved[0]).toMatchObject({
      profileId: 3,
      name: "Legacy Renamed",
      cutoff: 2,
      mustContain: ["x265"],
      mustNotContain: ["cam"],
      originalFormat: true,
    });
    expect(Array.isArray(saved[0].items)).toBe(true);
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

    await userEvent.click(saveButton());

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;

    expect(submitted["settings-general-serie_default_profile"]).toBe(1);
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

    await userEvent.click(saveButton());

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;

    expect(submitted["settings-general-remove_profile_tags"]).toEqual([
      "bad_tag123",
    ]);
  });
});
