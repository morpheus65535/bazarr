import { notifications } from "@mantine/notifications";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import {
  useLapseTestMutation,
  useSettingsMutation,
  useSystemSettings,
  useSystemStatus,
} from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsSubtitleProcessingView from "./index";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
    useSystemStatus: vitest.fn(),
    useLapseTestMutation: vitest.fn(),
  };
});

vi.mock("@mantine/notifications", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@mantine/notifications")>();
  return {
    ...actual,
    notifications: { ...actual.notifications, show: vitest.fn() },
  };
});

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;
const mockedUseSystemStatus = useSystemStatus as Mock;
const mockedUseLapseTestMutation = useLapseTestMutation as Mock;
const mockedNotificationsShow = notifications.show as Mock;
const mockTestLapse = vitest.fn();

const baseSettings = {
  general: {
    theme: "auto",
    use_whisper_fallback: true,
    use_whisper_fallback_series: true,
    use_whisper_fallback_on_import: true,
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
    concurrent_syncs: 1,
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
  mockedUseSystemStatus.mockReturnValue({
    data: { cpu_cores: 4 },
    isLoading: false,
    isRefetching: false,
  });
  mockedUseLapseTestMutation.mockReturnValue({
    mutateAsync: mockTestLapse,
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
    expect(
      screen.getByText(
        /Use Whisper as Fallback for Searches Triggered by Imports/i,
      ),
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

  describe("with LAPSE as the engine", () => {
    const renderLapse = async () => {
      setupMocks();
      mockedUseSystemSettings.mockReturnValue({
        data: {
          ...baseSettings,
          subsync: {
            ...baseSettings.subsync,
            engine: "lapse",
            lapse_url: "http://lapse:8080",
            lapse_path: "/usr/bin/lapse",
          },
        },
        isLoading: false,
        isRefetching: false,
      });
      customRender(<SettingsSubtitleProcessingView />);

      await userEvent.click(
        screen.getByTestId("section-toggle-Audio Synchronization"),
      );
    };

    it("hides the ffsubsync options and links the LAPSE docs", async () => {
      await renderLapse();

      expect(screen.getByText("Synchronization Reference")).toBeVisible();
      expect(
        screen.getByText("Do Not Fix Framerate Mismatch"),
      ).not.toBeVisible();
      expect(screen.getByText("Max Offset Seconds")).not.toBeVisible();
      expect(screen.getByText("Quality Max Offset Seconds")).not.toBeVisible();
      expect(
        screen.getByRole("link", { name: "Installing LAPSE for Bazarr" }),
      ).toHaveAttribute(
        "href",
        "https://github.com/Schwponaco-org/lapse/blob/main/docs/bazarr.md",
      );
    });

    it("tests LAPSE with the current URL and path", async () => {
      mockTestLapse.mockResolvedValueOnce({
        success: true,
        message: "Connected to LAPSE 2.5.1",
      });
      await renderLapse();

      expect(screen.getByRole("textbox", { name: "LAPSE URL" })).toHaveValue(
        "http://lapse:8080",
      );
      await userEvent.click(screen.getByRole("button", { name: "Test" }));

      expect(mockTestLapse).toHaveBeenCalledWith({
        url: "http://lapse:8080",
        path: "/usr/bin/lapse",
      });
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({ message: "Connected to LAPSE 2.5.1" }),
      );
    });

    it("shows why the test failed", async () => {
      mockTestLapse.mockResolvedValueOnce({
        success: false,
        message: "LAPSE executable not found",
      });
      await renderLapse();

      await userEvent.click(screen.getByRole("button", { name: "Test" }));

      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Connection failed",
          message: "LAPSE executable not found",
        }),
      );
    });
  });
});
