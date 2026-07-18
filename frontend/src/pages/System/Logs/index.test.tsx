import { fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useDeleteLogs, useSystemLogs, useSystemSettings } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { customRender, screen } from "@/tests";
import SystemLogsView from "./index";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemLogs: vitest.fn(),
    useDeleteLogs: vitest.fn(),
    useSystemSettings: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/site", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/site")>();
  return {
    ...actual,
    useInstanceName: vitest.fn(),
  };
});

const mockedUseSystemLogs = useSystemLogs as Mock;
const mockedUseDeleteLogs = useDeleteLogs as Mock;
const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseInstanceName = useInstanceName as Mock;

const baseSettings = {
  general: {
    instance_name: "Bazarr",
    debug: false,
  },
  log: {
    include_filter: "",
    exclude_filter: "",
    use_regex: false,
    ignore_case: false,
  },
} as unknown as Settings;

function setupMocks(
  logs: System.Log[] = [],
  settings?: Partial<Settings>,
  refetch?: ReturnType<typeof vitest.fn>,
  mutate?: ReturnType<typeof vitest.fn>,
) {
  mockedUseSystemLogs.mockReturnValue({
    data: logs,
    isLoading: false,
    isFetching: false,
    refetch: refetch ?? vitest.fn(),
    error: null,
  });
  mockedUseDeleteLogs.mockReturnValue({
    mutate: mutate ?? vitest.fn(),
    isPending: false,
  });
  mockedUseSystemSettings.mockReturnValue({
    data: { ...baseSettings, ...settings } as unknown as Settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseInstanceName.mockReturnValue("Bazarr");
}

function renderPage(
  logs: System.Log[] = [],
  settings?: Partial<Settings>,
  refetch?: ReturnType<typeof vitest.fn>,
  mutate?: ReturnType<typeof vitest.fn>,
) {
  setupMocks(logs, settings, refetch, mutate);
  return customRender(<SystemLogsView />);
}

describe("SystemLogsView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render logs in the table", async () => {
    renderPage([
      {
        type: "INFO",
        message: "Application started",
        timestamp: "2024-01-01T00:00:00",
      },
      {
        type: "ERROR",
        message: "Something went wrong",
        timestamp: "2024-01-01T00:01:00",
      },
    ]);

    expect(await screen.findByText("Application started")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("should open the exception detail modal", async () => {
    renderPage([
      {
        type: "ERROR",
        message: "Failure",
        timestamp: "2024-01-01T00:00:00",
        exception: "Error at foo\\nError at bar",
      },
    ]);

    const detailButton = await screen.findByRole("button", { name: "Detail" });

    await userEvent.click(detailButton);

    const modal = await screen.findByRole("dialog");

    expect(modal).toHaveTextContent("Stack Traceback");
    expect(modal).toHaveTextContent("Error at foo");
    expect(modal).toHaveTextContent("Error at bar");
  });

  it("should delete logs when clicking Empty", async () => {
    const mutate = vitest.fn();

    renderPage([], undefined, undefined, mutate);

    await userEvent.click(screen.getByRole("button", { name: "Empty" }));

    expect(mutate).toHaveBeenCalled();
  });

  it("should refresh logs when clicking Refresh", async () => {
    const refetch = vitest.fn();

    renderPage([], undefined, refetch);

    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));

    expect(refetch).toHaveBeenCalled();
  });

  it("should show the filter suffix badge for include and debug", () => {
    renderPage([], {
      general: {
        ...baseSettings.general,
        debug: true,
      } as Settings.General,
      log: {
        ...baseSettings.log,
        include_filter: "Include",
      } as Settings.Log,
    });

    expect(screen.getByText("Debug I")).toBeInTheDocument();
  });

  it("should show the filter suffix badge for exclude", () => {
    renderPage([], {
      log: {
        ...baseSettings.log,
        exclude_filter: "Exclude",
      } as Settings.Log,
    });

    expect(screen.getByText("E")).toBeInTheDocument();
  });

  it("should show the filter suffix badge for both filters", () => {
    renderPage([], {
      log: {
        ...baseSettings.log,
        include_filter: "Include",
        exclude_filter: "Exclude",
      } as Settings.Log,
    });

    expect(screen.getByText("I/E")).toBeInTheDocument();
  });

  it("should render the default icon for an unknown log type", async () => {
    renderPage([
      {
        type: "UNKNOWN" as System.LogType,
        message: "Unknown log",
        timestamp: "2024-01-01T00:00:00",
      },
    ]);

    expect(await screen.findByText("Unknown log")).toBeInTheDocument();
  });

  it("should render a debug log", async () => {
    renderPage([
      {
        type: "DEBUG",
        message: "Debug message",
        timestamp: "2024-01-01T00:00:00",
      },
    ]);

    expect(await screen.findByText("Debug message")).toBeInTheDocument();
  });

  it("should render a warning log", async () => {
    renderPage([
      {
        type: "WARNING",
        message: "Warning message",
        timestamp: "2024-01-01T00:00:00",
      },
    ]);

    expect(await screen.findByText("Warning message")).toBeInTheDocument();
  });

  it("should close the filter modal", async () => {
    renderPage([]);

    await userEvent.click(screen.getByRole("button", { name: "Filter" }));

    await screen.findByRole("dialog");

    await userEvent.click(screen.getByRole("button", { name: "Close" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("should open the filter modal", async () => {
    renderPage([]);

    await userEvent.click(screen.getByRole("button", { name: "Filter" }));

    const modal = await screen.findByRole("dialog");

    expect(modal).toHaveTextContent("Set Log Debug and Filter Options");
    expect(modal).toHaveTextContent("Include Filter");
    expect(modal).toHaveTextContent("Exclude Filter");
  });

  it("should download logs when clicking Download", () => {
    const open = vitest.fn();
    vi.stubGlobal("open", open);

    renderPage([]);

    fireEvent.click(screen.getByRole("button", { name: "Download" }));

    expect(open).toHaveBeenCalledWith(expect.stringContaining("/bazarr.log"));

    vi.unstubAllGlobals();
  });
});
