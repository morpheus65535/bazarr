import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsSubtitleProcessingView from "./index";

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
    use_whisper_fallback: true,
    use_whisper_fallback_series: true,
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
  return customRender(<SettingsSubtitleProcessingView />);
};

describe("SettingsSubtitleProcessingView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders the four advanced section headers", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Whisper As Fallback" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Sub-Zero Subtitle Content Modifications",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Audio Synchronization" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Custom Post-Processing" }),
    ).toBeInTheDocument();
  });

  it("renders feature controls inside the sections", async () => {
    renderPage();

    expect(
      screen.getByText(/Use Whisper as Fallback for Single Series Searches/i),
    ).toBeInTheDocument();

    // The post-processing command field lives in a collapsed section.
    expect(
      screen.getByRole("textbox", { name: "Command", hidden: true }),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByTestId("section-toggle-Custom Post-Processing"),
    );

    expect(screen.getByRole("textbox", { name: "Command" })).toBeVisible();
  });
});
