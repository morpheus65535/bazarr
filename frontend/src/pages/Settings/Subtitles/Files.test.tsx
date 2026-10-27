import { fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsSubtitlesFilesView from "./Files";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;

const baseSettings = {
  general: {
    theme: "auto",
    instance_name: "Bazarr",
    use_embedded_subs: true,
  },
} as unknown as Settings;

const setupMocks = () => {
  mockedUseSystemSettings.mockReturnValue({
    data: baseSettings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vitest.fn(),
    isPending: false,
  });
};

const renderPage = () => {
  setupMocks();
  return customRender(<SettingsSubtitlesFilesView />);
};

describe("SettingsSubtitlesFilesView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render the file and embedded subtitles sections", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Subtitle File Options" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Embedded Subtitles Handling" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Embedded Subtitles video parser/i),
    ).toBeInTheDocument();
  });

  it("should trigger onSaved when changing embedded subtitles parser", async () => {
    renderPage();

    // The embedded subtitles parser is the only labeled Select on the page
    // after the Subtitle Folder + Hearing-impaired selectors.
    const selects = screen.getAllByTestId("input-selector");
    const select = selects[2];

    await userEvent.click(select);

    const option = screen.getByRole("option", {
      hidden: true,
      name: /^mediainfo/i,
    });

    fireEvent.click(option);

    expect(select).toHaveValue(
      "mediainfo (slower but may give better results. User must install the mediainfo executable first)",
    );
  });
});
