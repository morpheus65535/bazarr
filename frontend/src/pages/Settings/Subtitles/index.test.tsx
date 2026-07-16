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
    use_whisper_fallback: true,
    use_whisper_fallback_series: true,
    upgrade_subs: true,
    adaptive_searching: true,
    use_subsync: true,
    use_postprocessing: true,
    use_postprocessing_threshold: true,
    use_postprocessing_threshold_movie: true,
  },
  subsync: {
    use_subsync: true,
    use_subsync_threshold: true,
    use_subsync_movie_threshold: true,
    force_audio: "true",
    use_original_language: true,
  },
  translator: {
    translator_type: "gemini",
    gemini_keys: ["key1"],
  },
} as unknown as Settings;

function setupMocks() {
  mockedUseSystemSettings.mockReturnValue({
    data: baseSettings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vitest.fn(),
    isPending: false,
  });
}

function renderPage() {
  setupMocks();
  return customRender(<SettingsSubtitlesView />);
}

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
      screen.getByText(/Use Whisper as Fallback for Single Series Searches/i),
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
    expect(
      screen.getByRole("textbox", { name: "Command" }),
    ).toBeInTheDocument();
  });

  it("should trigger onSaved when changing embedded subtitles parser", async () => {
    renderPage();

    // The embedded subtitles parser is the third unlabeled Select on the page.
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

  it("should sanitize Gemini API keys when removing a chip", async () => {
    renderPage();

    const chipInput = screen.getByRole("combobox", {
      name: "Gemini API keys",
    });

    await userEvent.click(chipInput);
    await userEvent.keyboard("{Backspace}");

    expect(screen.queryByText("key1")).not.toBeInTheDocument();
  });

  it("should trim whitespace when adding a Gemini API key", async () => {
    renderPage();

    const chipInput = screen.getByRole("combobox", {
      name: "Gemini API keys",
    });

    await userEvent.type(chipInput, "  key2  ");
    await userEvent.keyboard("{Enter}");

    expect(screen.getByText("key2")).toBeInTheDocument();
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
