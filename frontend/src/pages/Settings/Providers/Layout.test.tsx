import { useLocation, useNavigate } from "react-router";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { customRender, screen } from "@/tests";
import SettingsProvidersLayout from "./Layout";

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
  customRender(<SettingsProvidersLayout />);
  return navigate;
};

describe("SettingsProvidersLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the five tab labels", () => {
    mountAt("/settings/providers/subtitles");

    expect(screen.getByText("Subtitles")).toBeInTheDocument();
    expect(screen.getByText("Translation")).toBeInTheDocument();
    expect(screen.getByText("Protection")).toBeInTheDocument();
    expect(screen.getByText("Metadata")).toBeInTheDocument();
    expect(screen.getByText("Advanced")).toBeInTheDocument();
  });

  it("navigates to the clicked tab's nested route", async () => {
    const user = userEvent.setup();
    const navigate = mountAt("/settings/providers/subtitles");

    await user.click(screen.getByText("Metadata"));

    expect(navigate).toHaveBeenCalledWith("/settings/providers/metadata");
  });

  it("marks the active tab from the URL", () => {
    mountAt("/settings/providers/protection");

    const protectionTab = screen.getByRole("tab", { name: "Protection" });
    const subtitlesTab = screen.getByRole("tab", { name: "Subtitles" });

    expect(protectionTab).toHaveAttribute("data-active", "true");
    expect(subtitlesTab).not.toHaveAttribute("data-active", "true");
  });
});
