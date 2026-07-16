import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { task } from "@/modules/task";
import { customRender, screen } from "@/tests";
import SubtitleToolsMenu from "./SubtitleToolsMenu";

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

describe("SubtitleToolsMenu", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseSubtitleAction.mockReturnValue({
      mutateAsync: vitest.fn(),
    } as unknown as ReturnType<typeof useSubtitleAction>);
  });

  function renderMenu(
    props?: Partial<React.ComponentProps<typeof SubtitleToolsMenu>>,
  ) {
    const openContextModal = vitest.fn();
    const openConfirmModal = vitest.fn();

    mockUseModals.mockReturnValue({
      openContextModal,
      openConfirmModal,
      closeSelf: vitest.fn(),
      closeModal: vitest.fn(),
      openModal: vitest.fn(),
      closeAll: vitest.fn(),
    } as unknown as ReturnType<typeof useModals>);

    customRender(
      <SubtitleToolsMenu
        selections={[selection]}
        onAction={vitest.fn()}
        menu={{ withinPortal: false }}
        {...props}
      >
        <button>Open</button>
      </SubtitleToolsMenu>,
    );

    return { openContextModal, openConfirmModal };
  }

  it("processes a tool without a modal when clicked", async () => {
    renderMenu();
    const user = userEvent.setup();

    await user.click(screen.getByText("Open"));
    await user.click(await screen.findByText("Remove HI Tags"));

    expect(mockTaskCreate).toHaveBeenCalledTimes(1);
    expect(mockTaskCreate).toHaveBeenCalledWith(
      selection.path,
      "Remove HI Tags",
      expect.any(Function),
      expect.objectContaining({ action: "remove_HI" }),
    );
  });

  it("opens a modal tool when clicked", async () => {
    const { openContextModal } = renderMenu();
    const user = userEvent.setup();

    await user.click(screen.getByText("Open"));
    await user.click(await screen.findByText("Add Color..."));

    expect(openContextModal).toHaveBeenCalledTimes(1);
    expect(openContextModal).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({ selections: [selection] }),
    );
  });

  it("fires the search action when clicked", async () => {
    const onAction = vitest.fn();
    renderMenu({ selections: [], onAction });
    const user = userEvent.setup();

    await user.click(screen.getByText("Open"));
    await user.click(await screen.findByText("Search"));

    expect(onAction).toHaveBeenCalledWith("search");
  });

  it("opens the delete confirmation modal when clicked", async () => {
    const { openConfirmModal } = renderMenu();
    const user = userEvent.setup();

    await user.click(screen.getByText("Open"));
    await user.click(await screen.findByText("Delete..."));

    expect(openConfirmModal).toHaveBeenCalledTimes(1);
    expect(openConfirmModal).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "The following subtitles will be deleted",
      }),
    );
  });
});
