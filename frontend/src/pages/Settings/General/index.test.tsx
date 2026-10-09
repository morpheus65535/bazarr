import { useClipboard } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import {
  useSettingsMutation,
  useSystemSettings,
  useSystemStatus,
  useSystemWebhookTestMutation,
} from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsGeneralView from "./index";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
    useSystemStatus: vitest.fn(),
    useSystemWebhookTestMutation: vitest.fn(),
  };
});

vi.mock("@mantine/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@mantine/hooks")>();
  return {
    ...actual,
    useClipboard: vitest.fn(),
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
const mockedUseSystemStatus = useSystemStatus as Mock;
const mockedUseSystemWebhookTestMutation = useSystemWebhookTestMutation as Mock;
const mockedUseClipboard = useClipboard as Mock;
const mockedNotificationsShow = notifications.show as Mock;

const mockWebhookTest = vitest.fn().mockResolvedValue({
  data: { success: true, message: "ok" },
});

const baseSettings = {
  general: {
    theme: "auto",
    instance_name: "Bazarr",
    ip: "0.0.0.0",
    port: 6767,
    base_url: "/bazarr",
    concurrent_jobs: 2,
    enable_strm_support: false,
    use_external_webhook: true,
    debug: false,
    auto_update: false,
    branch: "master",
  },
  auth: {
    type: null,
    username: "",
    password: "",
    apikey: "existing-api-key",
  },
  log: {
    include_filter: "",
    exclude_filter: "",
    use_regex: false,
    ignore_case: false,
  },
  proxy: {
    type: null,
    url: "",
    port: null,
    username: "",
    password: "",
    exclude: [],
  },
  backup: {
    folder: "/backup",
    retention: 7,
    frequency: "weekly",
    day: 0,
    hour: 0,
  },
  analytics: {
    enabled: false,
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
  mockedUseSystemStatus.mockReturnValue({
    data: { cpu_cores: 4 },
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSystemWebhookTestMutation.mockReturnValue({
    mutateAsync: mockWebhookTest,
    isPending: false,
  });
  mockedUseClipboard.mockReturnValue({
    copy: vitest.fn(),
    copied: false,
    error: null,
  });
};

const renderPage = (clipboard?: {
  copy: typeof vitest.fn;
  copied: boolean;
  error: unknown;
}) => {
  setupMocks();
  if (clipboard) {
    mockedUseClipboard.mockReturnValue(clipboard);
  }
  return customRender(<SettingsGeneralView />);
};

describe("SettingsGeneralView", () => {
  const originalScrollIntoView = window.HTMLElement.prototype.scrollIntoView;

  beforeAll(() => {
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  afterAll(() => {
    window.HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
  });

  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("should render all general sections and hide updates when updates are disabled", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Host" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Security" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Jobs Manager" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Incoming Webhooks" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Proxy" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Analytics" }),
    ).toBeInTheDocument();
  });

  it("should expand authentication fields when selecting a security type", async () => {
    renderPage();

    expect(
      screen.queryByRole("textbox", { name: "Username" }),
    ).not.toBeInTheDocument();

    const authSelect = screen.getByRole("combobox", { name: "Authentication" });

    await userEvent.click(authSelect);

    const option = screen.getByRole("option", { hidden: true, name: "Basic" });

    fireEvent.click(option);

    expect(
      screen.getByRole("textbox", { name: "Username" }),
    ).toBeInTheDocument();
  });

  it("should generate a new API key when clicking regenerate", async () => {
    renderPage();

    const apiKeyInput = screen.getByRole("textbox", { name: "API Key" });

    expect(apiKeyInput).toHaveValue("existing-api-key");

    const regenerateButton = screen.getByRole("button", { name: "Regenerate" });

    await userEvent.click(regenerateButton);

    expect(apiKeyInput).not.toHaveValue("existing-api-key");
    expect((apiKeyInput as HTMLInputElement).value).toMatch(/^[a-f0-9]{32}$/);
  });

  it("should populate concurrent jobs based on CPU cores", () => {
    renderPage();

    expect(
      screen.getByRole("option", { hidden: true, name: "1 job" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { hidden: true, name: "4 jobs" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("option", { hidden: true, name: "5 jobs" }),
    ).not.toBeInTheDocument();
  });

  it("should call the webhook test mutation when clicking test connection", async () => {
    renderPage();

    const testButton = screen.getByRole("button", { name: "Test Connection" });

    await userEvent.click(testButton);

    expect(mockWebhookTest).toHaveBeenCalledTimes(1);
  });

  it("should show an error notification when the webhook test fails", async () => {
    mockWebhookTest.mockResolvedValueOnce({
      data: { success: false, message: "bad webhook" },
    });

    renderPage();

    const testButton = screen.getByRole("button", { name: "Test Connection" });

    await userEvent.click(testButton);

    await waitFor(() =>
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Error",
          message: "bad webhook",
          color: "danger",
        }),
      ),
    );
  });

  it("should show an error notification when the webhook test throws", async () => {
    mockWebhookTest.mockRejectedValueOnce(new Error("network error"));

    renderPage();

    const testButton = screen.getByRole("button", { name: "Test Connection" });

    await userEvent.click(testButton);

    await waitFor(() =>
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Error",
          message: "Failed to test external webhook connection",
          color: "danger",
        }),
      ),
    );
  });

  it("should copy the API key when in a secure context", async () => {
    const copyMock = vitest.fn();

    const originalIsSecureContext = window.isSecureContext;
    Object.defineProperty(window, "isSecureContext", {
      value: true,
      configurable: true,
    });

    renderPage({ copy: copyMock, copied: false, error: null });

    const copyButton = screen.getByRole("button", { name: "Copy API Key" });

    await userEvent.click(copyButton);

    expect(copyMock).toHaveBeenCalledWith("existing-api-key");

    Object.defineProperty(window, "isSecureContext", {
      value: originalIsSecureContext,
      configurable: true,
    });
  });

  it("should expand proxy fields when a proxy type is selected", async () => {
    renderPage();

    expect(
      screen.queryByRole("textbox", { name: "Host" }),
    ).not.toBeInTheDocument();

    const selects = screen.getAllByTestId("input-selector");
    const proxySelect = selects[selects.length - 1];

    await userEvent.click(proxySelect);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Socks5 (local DNS)",
    });

    fireEvent.click(option);

    expect(screen.getByRole("textbox", { name: "Host" })).toBeInTheDocument();
  });

  it("should submit the base URL with a leading slash", async () => {
    renderPage();

    const baseUrlInput = screen.getByRole("textbox", { name: "Base URL" });

    await userEvent.clear(baseUrlInput);
    await userEvent.type(baseUrlInput, "newbase");

    await userEvent.click(screen.getByRole("button", { name: /^Save/ }));

    const mutate =
      mockedUseSettingsMutation.mock.results[
        mockedUseSettingsMutation.mock.results.length - 1
      ].value.mutate;

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        "settings-general-base_url": "/newbase",
      }),
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });
});
