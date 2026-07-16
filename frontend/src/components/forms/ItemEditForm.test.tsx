import { describe, expect, it, vitest } from "vitest";
import { UseMutationResult } from "@tanstack/react-query";
import { useLanguageProfiles } from "@/apis/hooks";
import { customRender, screen, waitFor } from "@/tests";
import userEvent from "@testing-library/user-event";
import { useModals } from "@/modules/modals";
import ItemEditForm from "./ItemEditForm";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return { ...actual, useLanguageProfiles: vitest.fn() };
});

vitest.mock("@/modules/modals", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/modules/modals")>();
  return { ...actual, useModals: vitest.fn() };
});

const mockUseLanguageProfiles = vitest.mocked(useLanguageProfiles);
const mockUseModals = vitest.mocked(useModals);

const profiles = [
  { profileId: 1, name: "English" },
  { profileId: 2, name: "French" },
];

const item = {
  profileId: 1,
  audioLanguage: [{ code2: "en", name: "English" }],
  radarrId: 5,
  title: "Movie Title",
  path: "/movie/path",
  sceneName: "movie.scene",
  subtitles: [],
  missingSubtitles: [],
  tags: [],
  monitored: true,
  year: "2024",
  description: "",
  sortTitle: "Movie Title",
  subtitlesCount: 0,
} as unknown as Item.Base;

describe("ItemEditForm", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  function renderForm(
    props?: Partial<React.ComponentProps<typeof ItemEditForm>>,
  ) {
    const closeSelf = vitest.fn();
    mockUseModals.mockReturnValue({
      closeSelf,
    } as unknown as ReturnType<typeof useModals>);
    mockUseLanguageProfiles.mockReturnValue({
      data: profiles,
      isFetching: false,
    } as unknown as ReturnType<typeof useLanguageProfiles>);

    const mutate = vitest.fn();
    const mutation = {
      mutate,
      isPending: false,
    } as unknown as UseMutationResult<
      void,
      unknown,
      FormType.ModifyItem,
      unknown
    >;

    const onComplete = vitest.fn();
    const onCancel = vitest.fn();

    customRender(
      <ItemEditForm
        mutation={mutation}
        item={item}
        onComplete={onComplete}
        onCancel={onCancel}
        {...props}
      />,
    );

    return { mutation, mutate, onComplete, onCancel, closeSelf };
  }

  it("renders the form with the profile selector", () => {
    renderForm();

    expect(screen.getByText("Languages Profile")).toBeInTheDocument();
    expect(screen.getByText("Audio Languages")).toBeInTheDocument();
  });

  it("submits the form and saves the profile", async () => {
    const { mutate, onComplete, closeSelf } = renderForm();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(mutate).toHaveBeenCalledTimes(1);

    const mutateArgs = mutate.mock.calls[0];
    const payload = mutateArgs[0];
    const options = mutateArgs[1];

    expect(payload).toMatchObject({
      id: [5],
      profileId: [profiles[0].profileId],
    });
    expect(options.onSuccess).toBeInstanceOf(Function);
    expect(options.onError).toBeInstanceOf(Function);

    options.onSuccess();

    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(closeSelf).toHaveBeenCalledTimes(1);
  });

  it("shows a notification on mutation error", async () => {
    const { mutate, onComplete, closeSelf } = renderForm();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Save" }));

    mutate.mock.calls[0][1].onError();

    expect(onComplete).not.toHaveBeenCalled();
    expect(closeSelf).not.toHaveBeenCalled();
  });

  it("cancels and closes the modal", async () => {
    const { onCancel, closeSelf } = renderForm();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(closeSelf).toHaveBeenCalledTimes(1);
  });

  it("shows an error when item has no valid id", async () => {
    const badItem = { ...item, radarrId: null as unknown as number };

    const { mutation } = renderForm({ item: badItem as Item.Base });
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(mutation.mutate).not.toHaveBeenCalled();
    expect(screen.getByText("Invalid profile")).toBeInTheDocument();
  });
});
