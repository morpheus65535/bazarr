import { notifications } from "@mantine/notifications";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import {
  useOpenAICompatibleTranslatorTestMutation,
  useSettingsMutation,
  useSystemSettings,
} from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsProvidersTranslationView from "./Translation";

vi.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
    useOpenAICompatibleTranslatorTestMutation: vitest.fn(),
  };
});

vi.mock("@mantine/notifications", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@mantine/notifications")>();
  return {
    ...actual,
    notifications: {
      ...actual.notifications,
      show: vitest.fn(),
    },
  };
});

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;
const mockedUseOpenAICompatibleTranslatorTestMutation =
  useOpenAICompatibleTranslatorTestMutation as Mock;
const mockedNotificationsShow = notifications.show as Mock;

const baseSettings = {
  general: {
    theme: "auto",
    instance_name: "Bazarr",
  },
  translator: {
    translator_type: "gemini",
    gemini_keys: ["key1"],
  },
} as unknown as Settings;

const openAISettings = {
  ...baseSettings,
  translator: {
    ...baseSettings.translator,
    translator_type: "openai_compatible",
    openai_base_url: "http://localhost:1234/v1",
    openai_model: "local-model",
    openai_api_key: "test-key",
    openai_timeout: 45,
  },
} as unknown as Settings;

const mockTestTranslator = vitest.fn();

const setupMocks = (settings: Settings = baseSettings) => {
  mockedUseSystemSettings.mockReturnValue({
    data: settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  });
  mockedUseOpenAICompatibleTranslatorTestMutation.mockReturnValue({
    mutateAsync: mockTestTranslator,
    isPending: false,
  });
};

const renderPage = (settings: Settings = baseSettings) => {
  setupMocks(settings);
  return customRender(<SettingsProvidersTranslationView />);
};

describe("SettingsProvidersTranslationView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders the Translating section header", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Translating" }),
    ).toBeInTheDocument();
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

  it("tests the OpenAI-compatible translator with the current settings", async () => {
    mockTestTranslator.mockResolvedValueOnce({
      success: true,
      message: "Connection successful. Test translation: Bonjour",
    });
    renderPage(openAISettings);

    await userEvent.click(
      screen.getByRole("button", { name: "Test Connection" }),
    );

    expect(mockTestTranslator).toHaveBeenCalledWith({
      baseUrl: "http://localhost:1234/v1",
      model: "local-model",
      apiKey: "test-key",
      timeout: 45,
    });
    expect(mockedNotificationsShow).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Connection successful",
        message: "Connection successful. Test translation: Bonjour",
        color: "success",
      }),
    );
  });

  it("shows the endpoint error returned by the connection test", async () => {
    mockTestTranslator.mockResolvedValueOnce({
      success: false,
      message: "Authentication failed; check the API key",
    });
    renderPage(openAISettings);

    await userEvent.click(
      screen.getByRole("button", { name: "Test Connection" }),
    );

    expect(mockedNotificationsShow).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Connection failed",
        message: "Authentication failed; check the API key",
        color: "danger",
      }),
    );
  });

  it("disables the connection test when its URL or model is missing", () => {
    renderPage({
      ...openAISettings,
      translator: {
        ...openAISettings.translator,
        openai_base_url: "",
      },
    } as Settings);

    expect(
      screen.getByRole("button", { name: "Test Connection" }),
    ).toBeDisabled();
  });
});
