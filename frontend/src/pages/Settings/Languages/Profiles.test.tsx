import { fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import SettingsLanguageProfilesView from "./Profiles";
import {
  baseLanguages,
  baseProfiles,
  baseSettings,
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
      screen.queryByRole("button", { name: "No Enabled Languages" }),
    ).not.toBeInTheDocument();
  });

  it("should reveal the profile table after enabling a language inline", async () => {
    renderPage({
      languages: baseLanguages.map((l) => ({ ...l, enabled: false })),
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
      screen.getByRole("button", { name: "Add New Profile" }),
    ).toBeEnabled();
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

    await userEvent.click(modalScope.getByRole("button", { name: "Confirm" }));

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

    await userEvent.click(modalScope.getByRole("button", { name: "Confirm" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    expect(screen.getByText("Updated Profile")).toBeInTheDocument();
    expect(screen.queryByText("My Profile")).not.toBeInTheDocument();
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

    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

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

    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;

    expect(submitted["settings-general-remove_profile_tags"]).toEqual([
      "bad_tag123",
    ]);
  });
});
