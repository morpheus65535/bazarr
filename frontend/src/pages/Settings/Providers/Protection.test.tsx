import { fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsProvidersProtectionView from "./Protection";

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
    anti_captcha_provider: null,
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
  return customRender(<SettingsProvidersProtectionView />);
};

describe("SettingsProvidersProtectionView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders the anti-captcha options section", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Anti-Captcha Options" }),
    ).toBeInTheDocument();
  });

  it("should expand anti-captcha fields when selecting a provider", async () => {
    renderPage();

    const antiCaptchaSelect = screen.getByRole("combobox", {
      name: "Choose the anti-captcha provider you want to use",
    });

    await userEvent.click(antiCaptchaSelect);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Anti-Captcha",
    });

    fireEvent.click(option);

    expect(
      screen.getByRole("textbox", { name: "Account Key" }),
    ).toBeInTheDocument();
  });
});
