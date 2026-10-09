import { within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { customRender, screen } from "@/tests";
import SettingsProvidersMetadataView from "./Metadata";

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
    enabled_integrations: [] as string[],
  },
};

const setupMocks = (overrides?: Partial<typeof baseSettings>) => {
  mockedUseSystemSettings.mockReturnValue({
    data: {
      ...baseSettings,
      ...overrides,
    } as unknown as Settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vitest.fn(),
    isPending: false,
  });
};

const renderPage = (overrides?: Partial<typeof baseSettings>) => {
  setupMocks(overrides);
  return customRender(<SettingsProvidersMetadataView />);
};

describe("SettingsProvidersMetadataView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders the metadata providers section", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Metadata Providers" }),
    ).toBeInTheDocument();
  });

  it("should render enabled integration cards", () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_integrations: ["anidb"],
      },
    });

    expect(screen.getByText("AniDB")).toBeInTheDocument();
  });

  it("should render an inline link within the integration message", async () => {
    renderPage({
      general: {
        ...baseSettings.general,
        enabled_integrations: ["anidb"],
      },
    });

    await userEvent.click(screen.getByRole("button", { name: /AniDB/i }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const link = modalScope.getByRole("link", { name: "AniDB" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "https://anidb.net/software/add");
  });
});
