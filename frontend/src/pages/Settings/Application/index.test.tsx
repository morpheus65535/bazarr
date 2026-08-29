import { useLocation, useNavigate } from "react-router";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { customRender, screen } from "@/tests";
import SettingsApplicationView from "./index";

vi.mock("react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router")>();
  return {
    ...actual,
    useLocation: vi.fn(),
    useNavigate: vi.fn(),
  };
});

const mockedUseLocation = useLocation as unknown as ReturnType<typeof vi.fn>;
const mockedUseNavigate = useNavigate as unknown as ReturnType<typeof vi.fn>;

const mountAt = (pathname: string) => {
  mockedUseLocation.mockReturnValue({
    pathname,
    search: "",
    hash: "",
    state: null,
    key: "default",
  });
  const navigate = vi.fn();
  mockedUseNavigate.mockReturnValue(navigate);
  customRender(<SettingsApplicationView />);
  return navigate;
};

describe("SettingsApplicationView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the four tab labels", () => {
    mountAt("/settings/application/general");

    expect(screen.getByText("General")).toBeInTheDocument();
    expect(screen.getByText("UI")).toBeInTheDocument();
    expect(screen.getByText("Scheduler")).toBeInTheDocument();
    expect(screen.getByText("Maintenance")).toBeInTheDocument();
  });

  it("navigates to the clicked tab's nested route", async () => {
    const user = userEvent.setup();
    const navigate = mountAt("/settings/application/general");

    await user.click(screen.getByText("Scheduler"));

    expect(navigate).toHaveBeenCalledWith("/settings/application/scheduler");
  });

  it("marks the active tab from URLs with a trailing slash", () => {
    mountAt("/settings/application/maintenance/");

    const maintenanceTab = screen.getByRole("tab", { name: "Maintenance" });
    const generalTab = screen.getByRole("tab", { name: "General" });

    expect(maintenanceTab).toHaveAttribute("data-active", "true");
    expect(generalTab).not.toHaveAttribute("data-active", "true");
    expect(screen.getByRole("tabpanel")).toBeInTheDocument();
  });
});
