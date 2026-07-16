import { waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import api from "@/apis/raw";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsNotificationsView from "./index";

vi.mock("@/apis/raw", () => ({
  default: {
    system: {
      testNotification: vitest.fn(() => Promise.resolve()),
    },
  },
}));

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
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
    dont_notify_manual_actions: false,
    notify_if_nothing_is_missing_for_signalr_event: false,
  },
  notifications: {
    providers: [] as Settings.NotificationInfo[],
  },
};

const baseProviders: Settings.NotificationInfo[] = [
  { name: "Discord", enabled: false, url: "" },
  { name: "Email", enabled: false, url: "" },
  { name: "JSON", enabled: false, url: "" },
];

function setupMocks(
  overrides?: Partial<typeof baseSettings>,
  mutate?: ReturnType<typeof vitest.fn>,
) {
  mockedUseSystemSettings.mockReturnValue({
    data: {
      ...baseSettings,
      ...overrides,
    } as unknown as Settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: mutate ?? vitest.fn(),
    isPending: false,
  });
}

function renderPage(
  overrides?: Partial<typeof baseSettings>,
  mutate?: ReturnType<typeof vitest.fn>,
) {
  setupMocks(overrides, mutate);
  return customRender(<SettingsNotificationsView />);
}

describe("SettingsNotificationsView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render notification sections and options", () => {
    renderPage();

    expect(
      screen.getByRole("heading", { name: "Notifications" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Options" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("switch", { name: "Silent for Manual Actions" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("switch", {
        name: "Notify when there are no missing subtitles",
      }),
    ).toBeInTheDocument();
  });

  it("should render enabled notification providers as cards", () => {
    renderPage({
      notifications: {
        providers: [
          {
            name: "Discord",
            enabled: true,
            url: "https://discord.com/api/webhooks/...",
          },
          {
            name: "Email",
            enabled: false,
            url: "",
          },
        ],
      },
    });

    expect(screen.getByText("Discord")).toBeInTheDocument();
    expect(screen.queryByText("Email")).not.toBeInTheDocument();
  });

  it("should add a notification provider from the modal", async () => {
    renderPage({
      notifications: {
        providers: baseProviders,
      },
    });

    await userEvent.click(screen.getByRole("button", { name: "Add" }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const selector = modalScope.getByTestId("input-selector");

    await userEvent.click(selector);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Discord",
    });

    await userEvent.click(option);

    const urlInput = modalScope.getByPlaceholderText("URL");

    await userEvent.type(urlInput, "https://discord.com/api/webhooks/...");

    await userEvent.click(modalScope.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    expect(screen.getByText("Discord")).toBeInTheDocument();
  });

  it("should remove a notification provider from the modal", async () => {
    renderPage({
      notifications: {
        providers: [
          { name: "Discord", enabled: true, url: "existing-url" },
          { name: "Email", enabled: false, url: "" },
        ],
      },
    });

    await userEvent.click(screen.getByText("Discord"));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    await userEvent.click(modalScope.getByRole("button", { name: "Remove" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    expect(screen.queryByText("Discord")).not.toBeInTheDocument();
  });

  it("should show custom notification help for JSON/XML/Form providers", async () => {
    renderPage({
      notifications: {
        providers: baseProviders,
      },
    });

    await userEvent.click(screen.getByRole("button", { name: "Add" }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const selector = modalScope.getByTestId("input-selector");

    await userEvent.click(selector);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "JSON",
    });

    await userEvent.click(option);

    expect(
      modalScope.getByText(/Customize the notification payload with/i),
    ).toBeInTheDocument();
    expect(modalScope.getByText(/media variables/i)).toBeInTheDocument();
  });

  it("should save providers using the notification hook", async () => {
    const mutate = vitest.fn();

    renderPage(
      {
        notifications: {
          providers: baseProviders,
        },
      },
      mutate,
    );

    await userEvent.click(screen.getByRole("button", { name: "Add" }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const selector = modalScope.getByTestId("input-selector");

    await userEvent.click(selector);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Discord",
    });

    await userEvent.click(option);

    const urlInput = modalScope.getByPlaceholderText("URL");

    await userEvent.type(urlInput, "https://discord.com/api/webhooks/...");

    await userEvent.click(modalScope.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    await userEvent.click(screen.getByRole("button", { name: /Save/ }));

    expect(mutate).toHaveBeenCalled();

    const submitted = mutate.mock.calls[0][0] as Record<string, unknown>;
    const providers = submitted["notifications-providers"] as string[];

    expect(providers).toContain(
      JSON.stringify({
        name: "Discord",
        enabled: true,
        url: "https://discord.com/api/webhooks/...",
      }),
    );
  });

  it("should test the notification URL", async () => {
    renderPage({
      notifications: {
        providers: baseProviders,
      },
    });

    await userEvent.click(screen.getByRole("button", { name: "Add" }));

    const modal = await screen.findByRole("dialog");
    const modalScope = within(modal);

    const selector = modalScope.getByTestId("input-selector");

    await userEvent.click(selector);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Discord",
    });

    await userEvent.click(option);

    const urlInput = modalScope.getByPlaceholderText("URL");

    await userEvent.type(urlInput, "https://discord.com/api/webhooks/...");

    await userEvent.click(modalScope.getByRole("button", { name: "Test" }));

    expect(api.system.testNotification).toHaveBeenCalledWith(
      "https://discord.com/api/webhooks/...",
    );
  });
});
