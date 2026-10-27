import { useLocation, useNavigate } from "react-router";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { customRender, screen } from "@/tests";
import SettingsSubtitlesLayout from "./Layout";

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
  customRender(<SettingsSubtitlesLayout />);
  return navigate;
};

describe("SettingsSubtitlesLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the three tab labels", () => {
    mountAt("/settings/subtitles/files");

    expect(screen.getByText("Files")).toBeInTheDocument();
    expect(screen.getByText("Search")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();
  });

  it("navigates to the clicked tab's nested route", async () => {
    const user = userEvent.setup();
    const navigate = mountAt("/settings/subtitles/files");

    await user.click(screen.getByText("Search"));

    expect(navigate).toHaveBeenCalledWith("/settings/subtitles/search");
  });

  it("marks the active tab from the URL", () => {
    mountAt("/settings/subtitles/processing");

    const processingTab = screen.getByRole("tab", { name: "Processing" });
    const filesTab = screen.getByRole("tab", { name: "Files" });

    expect(processingTab).toHaveAttribute("data-active", "true");
    expect(filesTab).not.toHaveAttribute("data-active", "true");
  });
});
