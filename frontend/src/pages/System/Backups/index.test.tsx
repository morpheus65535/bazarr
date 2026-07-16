import { customRender, screen, within } from "@/tests";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import {
  useCreateBackups,
  useDeleteBackups,
  useRestoreBackups,
  useSystemBackups,
} from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import SystemBackupsView from "./index";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemBackups: vitest.fn(),
    useCreateBackups: vitest.fn(),
    useDeleteBackups: vitest.fn(),
    useRestoreBackups: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/site", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/site")>();
  return {
    ...actual,
    useInstanceName: vitest.fn(),
  };
});

const mockedUseSystemBackups = useSystemBackups as Mock;
const mockedUseCreateBackups = useCreateBackups as Mock;
const mockedUseDeleteBackups = useDeleteBackups as Mock;
const mockedUseRestoreBackups = useRestoreBackups as Mock;
const mockedUseInstanceName = useInstanceName as Mock;

const baseBackup: System.Backups = {
  type: "backup",
  filename: "backup_20240101.zip",
  size: "1.2 MB",
  date: "2024-01-01 00:00:00",
  id: 1,
};

function setupMocks(
  backups: System.Backups[] = [],
  createMutate?: ReturnType<typeof vitest.fn>,
  restoreMutate?: ReturnType<typeof vitest.fn>,
  deleteMutate?: ReturnType<typeof vitest.fn>,
) {
  mockedUseSystemBackups.mockReturnValue({
    data: backups,
    isLoading: false,
    isFetching: false,
    refetch: vitest.fn(),
    error: null,
  });
  mockedUseCreateBackups.mockReturnValue({
    mutate: createMutate ?? vitest.fn(),
    isPending: false,
  });
  mockedUseRestoreBackups.mockReturnValue({
    mutate: restoreMutate ?? vitest.fn(),
    isPending: false,
  });
  mockedUseDeleteBackups.mockReturnValue({
    mutate: deleteMutate ?? vitest.fn(),
    isPending: false,
  });
  mockedUseInstanceName.mockReturnValue("Bazarr");
}

function renderPage(
  backups: System.Backups[] = [],
  createMutate?: ReturnType<typeof vitest.fn>,
  restoreMutate?: ReturnType<typeof vitest.fn>,
  deleteMutate?: ReturnType<typeof vitest.fn>,
) {
  setupMocks(backups, createMutate, restoreMutate, deleteMutate);
  return customRender(<SystemBackupsView />);
}

describe("SystemBackupsView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render backups in the table", async () => {
    renderPage([baseBackup]);

    expect(await screen.findByText("backup_20240101.zip")).toBeInTheDocument();
    expect(screen.getByText("1.2 MB")).toBeInTheDocument();
    expect(screen.getByText("2024-01-01 00:00:00")).toBeInTheDocument();
  });

  it("should create a backup when clicking Backup Now", async () => {
    const createMutate = vitest.fn();

    renderPage([], createMutate);

    await userEvent.click(screen.getByRole("button", { name: "Backup Now" }));

    expect(createMutate).toHaveBeenCalled();
  });

  it("should restore a backup after confirming", async () => {
    const restoreMutate = vitest.fn();

    renderPage([baseBackup], undefined, restoreMutate);

    await userEvent.click(screen.getByRole("button", { name: "Restore" }));

    const modal = await screen.findByRole("dialog");

    await userEvent.click(
      within(modal).getByRole("button", { name: "Restore" }),
    );

    expect(restoreMutate).toHaveBeenCalledWith("backup_20240101.zip");
  });

  it("should delete a backup after confirming", async () => {
    const deleteMutate = vitest.fn();

    renderPage([baseBackup], undefined, undefined, deleteMutate);

    await userEvent.click(screen.getByRole("button", { name: "Delete" }));

    const modal = await screen.findByRole("dialog");

    await userEvent.click(
      within(modal).getByRole("button", { name: "Delete" }),
    );

    expect(deleteMutate).toHaveBeenCalledWith("backup_20240101.zip");
  });
});
