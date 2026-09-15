import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsProvidersAdvancedView from "./Advanced";

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
    disable_all_providers_ssl_verify: false,
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
  return customRender(<SettingsProvidersAdvancedView />);
};

describe("SettingsProvidersAdvancedView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders the advanced section with the SSL validation option", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Advanced" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("switch", {
        name: "Disable All Providers HTTPS Certificate Validation",
      }),
    ).toBeInTheDocument();
  });
});
