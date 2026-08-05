import { Mock, vi, vitest } from "vitest";
import { useSystemHealth, useSystemStatus } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { act, customRender, screen } from "@/tests";
import SystemStatusView from "./index";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemHealth: vitest.fn(),
    useSystemStatus: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/site", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/site")>();
  return {
    ...actual,
    useInstanceName: vitest.fn(),
  };
});

const mockedUseSystemHealth = useSystemHealth as Mock;
const mockedUseSystemStatus = useSystemStatus as Mock;
const mockedUseInstanceName = useInstanceName as Mock;

const baseStatus: System.Status = {
  bazarr_config_directory: "/config",
  bazarr_directory: "/bazarr",
  bazarr_version: "1.0.0",
  database_engine: "SQLite",
  database_migration: "1",
  operating_system: "Linux",
  package_version: "",
  python_version: "3.10",
  radarr_version: "4.0",
  sonarr_version: "3.0",
  start_time: 0,
  timezone: "UTC",
  cpu_cores: 4,
};

const setupMocks = (
  health: System.Health[] = [],
  status: Partial<System.Status> = {},
) => {
  mockedUseSystemHealth.mockReturnValue({
    data: health,
    isLoading: false,
    isFetching: false,
    refetch: vitest.fn(),
    error: null,
  });
  mockedUseSystemStatus.mockReturnValue({
    data: { ...baseStatus, ...status },
    isLoading: false,
  });
  mockedUseInstanceName.mockReturnValue("Bazarr");
};

const renderPage = (
  health: System.Health[] = [],
  status: Partial<System.Status> = {},
) => {
  setupMocks(health, status);
  return customRender(<SystemStatusView />);
};

describe("SystemStatusView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render status and health information", async () => {
    renderPage([{ object: "Sonarr", issue: "Sonarr is not running" }], {
      bazarr_version: "1.2.3",
    });

    expect(await screen.findByText("Bazarr Version")).toBeInTheDocument();
    expect(screen.getByText("1.2.3")).toBeInTheDocument();
    expect(screen.getByText("Sonarr is not running")).toBeInTheDocument();
  });

  it("should show the package version when it is set", () => {
    renderPage([], { package_version: "v1.0.0-package" });

    expect(screen.getByText("Package Version")).toBeInTheDocument();
    expect(screen.getByText("v1.0.0-package")).toBeInTheDocument();
  });

  it("should hide the package version when it is empty", () => {
    renderPage([], { package_version: "" });

    expect(screen.queryByText("Package Version")).not.toBeInTheDocument();
  });

  it("should update uptime on interval", () => {
    vi.useFakeTimers();

    const startTime = Math.floor(Date.now() / 1000) - 3661;

    renderPage([], { start_time: startTime });

    act(() => {
      vi.advanceTimersByTime(1100);
    });

    expect(screen.getByText("Uptime")).toBeInTheDocument();
    expect(screen.getByText(/0d 01:01:0/)).toBeInTheDocument();

    vi.useRealTimers();
  });
});
