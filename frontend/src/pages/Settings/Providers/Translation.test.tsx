import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsProvidersTranslationView from "./Translation";

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
  },
  translator: {
    translator_type: "gemini",
    gemini_keys: ["key1"],
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
});
