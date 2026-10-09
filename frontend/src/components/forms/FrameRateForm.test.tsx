import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { task } from "@/modules/task";
import { customRender, screen } from "@/tests";
import FrameRateForm from "./FrameRateForm";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return { ...actual, useSubtitleAction: vitest.fn() };
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
const mockUseModals = vitest.mocked(useModals);
const mockTaskCreate = vitest.mocked(task.create);

const selection = {
  id: 1,
  subtitlesId: 2,
  type: "episode",
  language: "en",
  path: "/subtitles/sub.srt",
  hi: "False",
  forced: "False",
} as FormType.ModifySubtitle;

describe("FrameRateForm", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  const renderForm = (
    props?: Partial<React.ComponentProps<typeof FrameRateForm>>,
  ) => {
    const closeSelf = vitest.fn();
    mockUseModals.mockReturnValue({
      closeSelf,
    } as unknown as ReturnType<typeof useModals>);
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync: vitest.fn(),
    } as unknown as ReturnType<typeof useSubtitleAction>);

    customRender(<FrameRateForm selections={[selection]} {...props} />);

    return { closeSelf };
  };

  it("submits the form and creates a task for each selection", async () => {
    const onSubmit = vitest.fn();
    const { closeSelf } = renderForm({ onSubmit });
    const user = userEvent.setup();

    const fromInput = screen.getByPlaceholderText("From");
    const toInput = screen.getByPlaceholderText("To");

    await user.clear(fromInput);
    await user.type(fromInput, "24");
    await user.clear(toInput);
    await user.type(toInput, "25");
    await user.click(screen.getByRole("button", { name: "Start" }));

    expect(mockTaskCreate).toHaveBeenCalledTimes(1);
    expect(mockTaskCreate).toHaveBeenCalledWith(
      selection.path,
      "Changing Frame Rate",
      expect.any(Function),
      expect.objectContaining({
        action: "change_FPS(from=24,to=25)",
        form: selection,
      }),
    );
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(closeSelf).toHaveBeenCalledTimes(1);
  });
});
