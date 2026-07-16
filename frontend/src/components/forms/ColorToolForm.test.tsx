import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { task } from "@/modules/task";
import { customRender, screen } from "@/tests";
import ColorToolForm from "./ColorToolForm";

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
  type: "episode",
  language: "en",
  path: "/subtitles/sub.srt",
  hi: "False",
  forced: "False",
} as FormType.ModifySubtitle;

describe("ColorToolForm", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  function renderForm(
    props?: Partial<React.ComponentProps<typeof ColorToolForm>>,
  ) {
    const closeSelf = vitest.fn();
    mockUseModals.mockReturnValue({
      closeSelf,
    } as unknown as ReturnType<typeof useModals>);
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync: vitest.fn(),
    } as unknown as ReturnType<typeof useSubtitleAction>);

    customRender(<ColorToolForm selections={[selection]} {...props} />);

    return { closeSelf };
  }

  it("submits the form and creates a color task", async () => {
    const onSubmit = vitest.fn();
    const { closeSelf } = renderForm({ onSubmit });
    const user = userEvent.setup();

    await user.click(screen.getByTestId("input-selector"));
    await user.click(screen.getByText("Red"));
    await user.click(screen.getByRole("button", { name: "Start" }));

    expect(mockTaskCreate).toHaveBeenCalledTimes(1);
    expect(mockTaskCreate).toHaveBeenCalledWith(
      selection.path,
      "Changing Color",
      expect.any(Function),
      expect.objectContaining({
        action: "color(name=red)",
        form: selection,
      }),
    );
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(closeSelf).toHaveBeenCalledTimes(1);
  });
});
