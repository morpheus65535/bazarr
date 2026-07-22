import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import {
  useRefTracksByEpisodeId,
  useRefTracksByMovieId,
  useSubtitleAction,
} from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { customRender, screen, waitFor } from "@/tests";
import SyncSubtitleForm from "./SyncSubtitleForm";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSubtitleAction: vitest.fn(),
    useRefTracksByMovieId: vitest.fn(),
    useRefTracksByEpisodeId: vitest.fn(),
  };
});

vitest.mock("@/modules/modals", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/modules/modals")>();
  return { ...actual, useModals: vitest.fn() };
});

vitest.mock("@/modules/task", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/modules/task")>();
  return { ...actual, task: { create: vitest.fn() } };
});

const mockUseSubtitleAction = vitest.mocked(useSubtitleAction);
const mockUseRefTracksByMovieId = vitest.mocked(useRefTracksByMovieId);
const mockUseRefTracksByEpisodeId = vitest.mocked(useRefTracksByEpisodeId);
const mockUseModals = vitest.mocked(useModals);

const selection = {
  id: 1,
  subtitlesId: 2,
  type: "episode",
  language: "en",
  path: "/subtitles/sub.srt",
  hi: "False",
  forced: "False",
} as FormType.ModifySubtitle;

describe("SyncSubtitleForm", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseRefTracksByMovieId.mockReturnValue({
      data: undefined,
    } as unknown as ReturnType<typeof useRefTracksByMovieId>);
    mockUseRefTracksByEpisodeId.mockReturnValue({
      data: undefined,
    } as unknown as ReturnType<typeof useRefTracksByEpisodeId>);
  });

  function renderForm(
    props?: Partial<React.ComponentProps<typeof SyncSubtitleForm>>,
  ) {
    const closeSelf = vitest.fn();
    mockUseModals.mockReturnValue({
      closeSelf,
    } as unknown as ReturnType<typeof useModals>);

    customRender(<SyncSubtitleForm selections={[selection]} {...props} />);

    return { closeSelf };
  }

  it("renders the form and submits the sync", async () => {
    const mutateAsync = vitest.fn().mockResolvedValue(undefined);
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useSubtitleAction>);
    const onSubmit = vitest.fn();
    const { closeSelf } = renderForm({ onSubmit });
    const user = userEvent.setup();

    await user.click(screen.getByText("Sync"));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalled();
    });
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(closeSelf).toHaveBeenCalledTimes(1);
  });
});
