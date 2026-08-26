import { fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsSubtitlesView from "./index";

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
    adaptive_searching: true,
    upgrade_subs: true,
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
  return customRender(<SettingsSubtitlesView />);
};

describe("SettingsSubtitlesView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render expanded subtitle sections", () => {
    renderPage();

    expect(
      screen.getByText(/Embedded Subtitles video parser/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Number of days to go back in history to upgrade subtitles/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /The delay from the first search to adaptive searching taking effect/i,
      ),
    ).toBeInTheDocument();
  });

  it("should trigger onSaved when changing embedded subtitles parser", async () => {
    renderPage();

    // The embedded subtitles parser is the only labeled Select on the page after
    // the Subtitle Folder + Hearing-impaired selectors.
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

  it("should trigger onSaved when selecting adaptive searching delay", async () => {
    renderPage();

    const selects = screen.getAllByTestId("input-selector");
    const delaySelect = selects[3];

    await userEvent.click(delaySelect);

    const options = screen.getAllByRole("option", {
      hidden: true,
      name: "3 weeks",
    });

    fireEvent.click(options[0]);

    expect(delaySelect).toHaveValue("3 weeks");
  });

  it("should trigger onSaved when selecting adaptive searching delta", async () => {
    renderPage();

    const selects = screen.getAllByTestId("input-selector");
    const deltaSelect = selects[4];

    await userEvent.click(deltaSelect);

    const option = screen.getByRole("option", { hidden: true, name: "3 days" });

    fireEvent.click(option);

    expect(deltaSelect).toHaveValue("3 days");
  });
});
