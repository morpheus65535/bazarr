import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { task } from "@/modules/task";
import { customRender, screen } from "@/tests";
import TimeOffsetForm from "./TimeOffsetForm";

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

describe("TimeOffsetForm", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  const renderForm = (
    props?: Partial<React.ComponentProps<typeof TimeOffsetForm>>,
  ) => {
    const closeSelf = vitest.fn();
    mockUseModals.mockReturnValue({
      closeSelf,
    } as unknown as ReturnType<typeof useModals>);
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync: vitest.fn(),
    } as unknown as ReturnType<typeof useSubtitleAction>);

    customRender(<TimeOffsetForm selections={[selection]} {...props} />);

    return { closeSelf };
  };

  it("submits the form with a positive offset", async () => {
    const onSubmit = vitest.fn();
    const { closeSelf } = renderForm({ onSubmit });
    const user = userEvent.setup();

    await user.clear(screen.getByLabelText("hour"));
    await user.type(screen.getByLabelText("hour"), "1");
    await user.click(screen.getByRole("button", { name: "Start" }));

    expect(mockTaskCreate).toHaveBeenCalledTimes(1);
    expect(mockTaskCreate).toHaveBeenCalledWith(
      selection.path,
      "Changing Time",
      expect.any(Function),
      expect.objectContaining({
        action: "shift_offset(h=1,m=0,s=0,ms=0)",
        form: selection,
      }),
    );
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(closeSelf).toHaveBeenCalledTimes(1);
  });

  it("submits the form with a negative offset", async () => {
    renderForm();
    const user = userEvent.setup();

    await user.click(screen.getAllByRole("button")[0]);
    await user.clear(screen.getByLabelText("min"));
    await user.type(screen.getByLabelText("min"), "5");
    await user.click(screen.getByRole("button", { name: "Start" }));

    expect(mockTaskCreate).toHaveBeenCalledTimes(1);
    expect(mockTaskCreate).toHaveBeenCalledWith(
      selection.path,
      "Changing Time",
      expect.any(Function),
      expect.objectContaining({
        action: "shift_offset(h=0,m=-5,s=0,ms=0)",
        form: selection,
      }),
    );
  });
});
