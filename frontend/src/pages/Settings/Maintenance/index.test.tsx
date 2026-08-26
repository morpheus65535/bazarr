import { vi } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import { Environment } from "@/utilities/env";
import SettingsMaintenanceView from "./index";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vi.fn(),
    useSettingsMutation: vi.fn(),
  };
});

const mockedUseSystemSettings = useSystemSettings as unknown as ReturnType<
  typeof vi.fn
>;
const mockedUseSettingsMutation = useSettingsMutation as unknown as ReturnType<
  typeof vi.fn
>;

const baseSettings = {
  general: {
    theme: "auto",
    auto_update: false,
    branch: "master",
    debug: false,
  },
  log: {
    include_filter: "",
    exclude_filter: "",
    use_regex: false,
    ignore_case: false,
  },
  backup: {
    folder: "/backup",
    retention: 7,
    frequency: "weekly",
    day: 0,
    hour: 0,
  },
  analytics: {
    enabled: false,
  },
} as unknown as Settings;

const setupMocks = () => {
  mockedUseSystemSettings.mockReturnValue({
    data: baseSettings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  });
};

const renderPage = () => {
  setupMocks();
  return customRender(<SettingsMaintenanceView />);
};

describe("SettingsMaintenanceView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Logging and Analytics sections", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Logging" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Analytics" }),
    ).toBeInTheDocument();
  });

  it("hides the Updates section when updates are disabled", () => {
    renderPage();

    expect(
      screen.queryByRole("heading", { name: "Updates" }),
    ).not.toBeInTheDocument();
  });

  it("shows the Updates section when updates are enabled", () => {
    const canUpdateSpy = vi
      .spyOn(Environment, "canUpdate", "get")
      .mockReturnValue(true);

    renderPage();

    expect(
      screen.getByRole("heading", { name: "Updates" }),
    ).toBeInTheDocument();

    canUpdateSpy.mockRestore();
  });
});
