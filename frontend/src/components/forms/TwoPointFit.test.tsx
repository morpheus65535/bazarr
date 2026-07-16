import { describe, expect, it, vitest } from "vitest";
import { useSubtitleAction, useSubtitleContents } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import { useModals } from "@/modules/modals";
import { task } from "@/modules/task";
import TwoPointFitForm from "./TwoPointFit";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSubtitleAction: vitest.fn(),
    useSubtitleContents: vitest.fn(),
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

const mockUseSubtitleContents = vitest.mocked(useSubtitleContents);
const mockUseSubtitleAction = vitest.mocked(useSubtitleAction);
const mockUseModals = vitest.mocked(useModals);

const selection = {
  id: 1,
  type: "episode",
  language: "en",
  path: "/subtitles/sub.srt",
  hi: "False",
  forced: "False",
} as FormType.ModifySubtitle;

describe("TwoPointFitForm", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync: vitest.fn(),
    } as unknown as ReturnType<typeof useSubtitleAction>);
    mockUseModals.mockReturnValue({
      closeSelf: vitest.fn(),
    } as unknown as ReturnType<typeof useModals>);
  });

  function renderForm(
    props?: Partial<React.ComponentProps<typeof TwoPointFitForm>>,
  ) {
    customRender(<TwoPointFitForm selections={[selection]} {...props} />);
  }

  it("shows a loading overlay while subtitle contents are being fetched", () => {
    mockUseSubtitleContents.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as unknown as ReturnType<typeof useSubtitleContents>);

    renderForm();

    expect(screen.getByText("Align")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Align" })).toBeDisabled();
  });
});
