import { act } from "@testing-library/react";
import { describe, expect, it, vitest } from "vitest";
import {
  useRefTracksByEpisodeId,
  useRefTracksByMovieId,
  useSubtitleAction,
  useSystemSettings,
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
    useSystemSettings: vitest.fn(),
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
const mockUseSystemSettings = vitest.mocked(useSystemSettings);
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
    mockUseSystemSettings.mockReturnValue({
      data: undefined,
    } as unknown as ReturnType<typeof useSystemSettings>);
  });

  const renderForm = (
    props?: Partial<React.ComponentProps<typeof SyncSubtitleForm>>,
  ) => {
    const closeSelf = vitest.fn();
    mockUseModals.mockReturnValue({
      closeSelf,
    } as unknown as ReturnType<typeof useModals>);

    customRender(<SyncSubtitleForm selections={[selection]} {...props} />);

    return { closeSelf };
  };

  it("renders the form and submits the sync", async () => {
    const mutateAsync = vitest.fn().mockResolvedValue(undefined);
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useSubtitleAction>);
    const onSubmit = vitest.fn();
    const { closeSelf } = renderForm({ onSubmit });

    const submitButton = screen.getByRole("button", { name: "Sync" });
    await act(async () => {
      submitButton.click();
    });

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalled();
    });
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(closeSelf).toHaveBeenCalledTimes(1);
  });

  it("hides the ffsubsync options when LAPSE is the engine", () => {
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync: vitest.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useSubtitleAction>);
    mockUseSystemSettings.mockReturnValue({
      data: { general: { theme: "dark" }, subsync: { engine: "lapse" } },
    } as unknown as ReturnType<typeof useSystemSettings>);
    renderForm();

    expect(screen.getByText("Reference")).toBeInTheDocument();
    expect(screen.queryByText("Max Offset Seconds")).not.toBeInTheDocument();
    expect(screen.queryByText("Quality Checks")).not.toBeInTheDocument();
  });
});
