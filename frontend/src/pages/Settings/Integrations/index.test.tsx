import { useLocation, useNavigate } from "react-router";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsIntegrationsView from "./index";

vi.mock("react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useLocation: vi.fn(),
    useNavigate: vi.fn(),
  };
});

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemSettings: vi.fn(),
  };
});

const mockedUseLocation = useLocation as unknown as ReturnType<typeof vi.fn>;
const mockedUseNavigate = useNavigate as unknown as ReturnType<typeof vi.fn>;
const mockedUseSystemSettings = useSystemSettings as unknown as ReturnType<
  typeof vi.fn
>;

const mountAt = (pathname: string, settings?: Partial<Settings>) => {
  mockedUseLocation.mockReturnValue({
    pathname,
    search: "",
    hash: "",
    state: null,
    key: "default",
  });
  const navigate = vi.fn();
  mockedUseNavigate.mockReturnValue(navigate);
  mockedUseSystemSettings.mockReturnValue({
    data: settings,
    isLoading: false,
    isRefetching: false,
  });
  customRender(<SettingsIntegrationsView />);
  return navigate;
};

describe("SettingsIntegrationsView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all four integration tab labels", () => {
    mountAt("/settings/integrations/sonarr");

    expect(screen.getByText("Sonarr")).toBeInTheDocument();
    expect(screen.getByText("Radarr")).toBeInTheDocument();
    expect(screen.getByText("Plex")).toBeInTheDocument();
    expect(screen.getByText("Jellyfin")).toBeInTheDocument();
  });

  it("navigates to the clicked tab's nested route", async () => {
    const user = userEvent.setup();
    const navigate = mountAt("/settings/integrations/sonarr");

    const plexTab = screen.getByText("Plex");
    await user.click(plexTab);

    expect(navigate).toHaveBeenCalledWith("/settings/integrations/plex");
  });

  it("shows a status dot only on enabled integrations", () => {
    mountAt("/settings/integrations/sonarr", {
      general: { use_sonarr: true, use_plex: true } as Settings["general"],
    } as Partial<Settings>);

    expect(screen.getByTestId("tab-status-sonarr")).toBeInTheDocument();
    expect(screen.getByTestId("tab-status-plex")).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "Sonarr, enabled" }),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("tab-status-radarr")).not.toBeInTheDocument();
    expect(screen.queryByTestId("tab-status-jellyfin")).not.toBeInTheDocument();
  });

  it("renders the tab active state for the current URL", async () => {
    mountAt("/settings/integrations/radarr");

    const radarrTab = screen.getByRole("tab", { name: "Radarr" });
    const sonarrTab = screen.getByRole("tab", { name: "Sonarr" });

    expect(radarrTab).toHaveAttribute("data-active", "true");
    expect(sonarrTab).not.toHaveAttribute("data-active", "true");
  });
});
