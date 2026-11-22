import { fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import ProfileEditor from "./index";

const item = (id: number, language: string): Language.ProfileItem => ({
  id,
  language,
  audioExclude: "False",
  audioOnlyInclude: "False",
  hi: "False",
  forced: "False",
});

const languages: Language.Info[] = [
  { code2: "en", name: "English" },
  { code2: "fr", name: "French" },
  { code2: "de", name: "German" },
  { code2: "it", name: "Italian" },
];

const enhancedProfile: Language.Profile = {
  profileId: 2,
  name: "Enhanced Profile",
  tag: undefined,
  profileType: "enhanced",
  items: [item(1, "en"), item(2, "fr"), item(3, "de"), item(4, "it")],
  groups: [
    { id: 1, operator: "AND", items: [item(1, "en"), item(2, "fr")] },
    { id: 2, operator: "OR", items: [item(3, "de"), item(4, "it")] },
  ],
  cutoff: 2,
  mustContain: [],
  mustNotContain: [],
  originalFormat: false,
};

const renderEditor = (
  profile: Language.Profile = enhancedProfile,
  overrides: Partial<{
    onApply: (value: Language.Profile) => void;
    onCancel: () => void;
    onDirtyChange: (isDirty: boolean) => void;
  }> = {},
) => {
  const onApply = overrides.onApply ?? vitest.fn();
  const onCancel = overrides.onCancel ?? vitest.fn();
  const onDirtyChange = overrides.onDirtyChange ?? vitest.fn();

  return {
    onApply,
    onCancel,
    onDirtyChange,
    ...customRender(
      <ProfileEditor
        profile={profile}
        languages={languages}
        isCreating={false}
        onApply={onApply}
        onCancel={onCancel}
        onDirtyChange={onDirtyChange}
      ></ProfileEditor>,
    ),
  };
};

const nameInput = () => screen.getByRole("textbox", { name: "Profile name" });

describe("ProfileEditor", () => {
  it("explains what the profile means and how it stops searching", () => {
    renderEditor();

    expect(screen.getByText("What this means")).toBeInTheDocument();
    expect(
      screen.getByText(/Stop searching once German or Italian is satisfied/i),
    ).toBeInTheDocument();
  });

  it("resets the stopping rule and explains it when its requirement is removed", async () => {
    renderEditor();

    await userEvent.click(
      screen.getByRole("button", { name: "Remove Requirement 2" }),
    );

    const modal = await screen.findByRole("dialog");

    await userEvent.click(
      within(modal).getByRole("button", { name: "Remove" }),
    );

    expect(
      await screen.findByText(/stopping rule was reset/i),
    ).toBeInTheDocument();
  });

  it("keeps the stopping rule on the same requirement after reordering", async () => {
    renderEditor();

    await userEvent.click(
      screen.getByRole("button", { name: "Move Requirement 1 down" }),
    );

    expect(
      screen.getByText(/Stop searching once German or Italian is satisfied/i),
    ).toBeInTheDocument();
  });

  it("applies the edited profile", async () => {
    const { onApply } = renderEditor();

    fireEvent.change(nameInput(), { target: { value: "Renamed" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({ name: "Renamed", profileType: "enhanced" }),
    );
  });

  it("reports a dirty draft to its container", async () => {
    const { onDirtyChange } = renderEditor();

    fireEvent.change(nameInput(), { target: { value: "Changed" } });

    await waitFor(() => expect(onDirtyChange).toHaveBeenLastCalledWith(true));
  });

  it("cancels without confirmation when nothing changed", async () => {
    const { onCancel } = renderEditor();

    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("sets the stopping rule from a requirement", async () => {
    renderEditor({ ...enhancedProfile, cutoff: null });

    expect(
      screen.getByText(/Keep searching until every unmet requirement/i),
    ).toBeInTheDocument();

    const toggles = screen.getAllByRole("button", {
      name: "Stop searching when this requirement is satisfied",
    });

    await userEvent.click(toggles[1]);

    expect(
      screen.getByText(/Stop searching once German or Italian is satisfied/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Stops searching")).toBeInTheDocument();
  });

  it("changes the match rule and explains it", async () => {
    renderEditor();

    expect(
      screen.getByText("Every language below must be found."),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getAllByRole("radio", { name: "Any language" })[0],
    );

    expect(
      screen.queryByText("Every language below must be found."),
    ).not.toBeInTheDocument();
    expect(
      screen.getAllByText("Any single language below is enough."),
    ).toHaveLength(2);
  });

  it("summarises issues when applying an invalid profile", async () => {
    renderEditor();

    fireEvent.change(nameInput(), { target: { value: "" } });

    await userEvent.click(
      screen.getByRole("button", { name: "Apply changes" }),
    );

    expect(await screen.findByText("1 issue to fix")).toBeInTheDocument();
  });

  it("asks to confirm before abandoning a dirty draft on Escape", async () => {
    renderEditor();

    fireEvent.change(nameInput(), { target: { value: "Changed" } });
    await userEvent.keyboard("{Escape}");

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });
});
