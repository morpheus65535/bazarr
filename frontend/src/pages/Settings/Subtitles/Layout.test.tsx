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
    mountAt("/settings/subtitles/general");

    expect(screen.getByText("Files & Search")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();
    expect(screen.getByText("Translation")).toBeInTheDocument();
  });

  it("navigates to the clicked tab's nested route", async () => {
    const user = userEvent.setup();
    const navigate = mountAt("/settings/subtitles/general");

    await user.click(screen.getByText("Translation"));

    expect(navigate).toHaveBeenCalledWith("/settings/subtitles/translation");
  });

  it("marks the active tab from the URL", () => {
    mountAt("/settings/subtitles/processing");

    const processingTab = screen.getByRole("tab", { name: "Processing" });
    const generalTab = screen.getByRole("tab", { name: "Files & Search" });

    expect(processingTab).toHaveAttribute("data-active", "true");
    expect(generalTab).not.toHaveAttribute("data-active", "true");
  });
});
