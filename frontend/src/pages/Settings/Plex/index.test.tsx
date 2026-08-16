import { act } from "react";
import { fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Mock, vi, vitest } from "vitest";
import { useInstanceName } from "@/apis/hooks/site";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks/system";
import { customRender, screen } from "@/tests";
import SettingsPlexView from "./index";

vi.mock("@/apis/hooks/system", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/system")>();
  return {
    ...actual,
    useSystemSettings: vitest.fn(),
    useSettingsMutation: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/site", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/site")>();
  return {
    ...actual,
    useInstanceName: vitest.fn(),
  };
});

vi.mock("@/apis/hooks/plex", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/plex")>();
  return {
    ...actual,
    usePlexAuthValidationQuery: vitest.fn(),
    usePlexServersQuery: vitest.fn(),
    usePlexSelectedServerQuery: vitest.fn(),
    usePlexPinMutation: vitest.fn(),
    usePlexPinCheckQuery: vitest.fn(),
    usePlexLogoutMutation: vitest.fn(),
    usePlexServerSelectionMutation: vitest.fn(),
    usePlexLibrariesQuery: vitest.fn(),
    usePlexWebhookCreateMutation: vitest.fn(),
    usePlexWebhookListQuery: vitest.fn(),
    usePlexWebhookDeleteMutation: vitest.fn(),
    usePlexAutopulseConfigQuery: vitest.fn(),
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

import { notifications } from "@mantine/notifications";
import {
  usePlexAuthValidationQuery,
  usePlexAutopulseConfigQuery,
  usePlexLibrariesQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
  usePlexSelectedServerQuery,
  usePlexServerSelectionMutation,
  usePlexServersQuery,
  usePlexWebhookCreateMutation,
  usePlexWebhookDeleteMutation,
  usePlexWebhookListQuery,
} from "@/apis/hooks/plex";

const mockedUseSystemSettings = useSystemSettings as Mock;
const mockedUseSettingsMutation = useSettingsMutation as Mock;
const mockedUseInstanceName = useInstanceName as Mock;
const mockedUsePlexAuthValidationQuery = usePlexAuthValidationQuery as Mock;
const mockedUsePlexServersQuery = usePlexServersQuery as Mock;
const mockedUsePlexSelectedServerQuery = usePlexSelectedServerQuery as Mock;
const mockedUsePlexPinMutation = usePlexPinMutation as Mock;
const mockedUsePlexPinCheckQuery = usePlexPinCheckQuery as Mock;
const mockedUsePlexLogoutMutation = usePlexLogoutMutation as Mock;
const mockedUsePlexServerSelectionMutation =
  usePlexServerSelectionMutation as Mock;
const mockedUsePlexLibrariesQuery = usePlexLibrariesQuery as Mock;
const mockedUsePlexWebhookCreateMutation = usePlexWebhookCreateMutation as Mock;
const mockedUsePlexWebhookListQuery = usePlexWebhookListQuery as Mock;
const mockedUsePlexWebhookDeleteMutation = usePlexWebhookDeleteMutation as Mock;
const mockedUsePlexAutopulseConfigQuery = usePlexAutopulseConfigQuery as Mock;
const mockedNotificationsShow = notifications.show as Mock;

const mockLogoutMutate = vitest.fn((_, options) => {
  options?.onSuccess?.();
});
const mockCreateWebhook = vitest.fn();
const mockDeleteWebhook = vitest.fn();
const mockServerSelectionMutate = vitest.fn();
const mockRefetchAutopulse = vitest.fn();

const baseSettings: {
  general: Record<string, unknown>;
  plex: Record<string, unknown>;
} = {
  general: {
    theme: "auto",
    instance_name: "Bazarr",
    use_plex: true,
  },
  plex: {
    ip: "localhost",
    port: 32400,
    apikey: "plex-api-key",
    ssl: false,
    set_movie_added: false,
    set_episode_added: false,
    movie_library: [] as string[],
    series_library: [] as string[],
    update_movie_library: false,
    update_series_library: false,
  },
};

type HookOverrides = {
  auth?: Record<string, unknown>;
  servers?: Record<string, unknown>;
  selectedServer?: Record<string, unknown>;
  libraries?: Record<string, unknown>;
  webhooks?: Record<string, unknown>;
  autopulse?: Record<string, unknown>;
  pinCheck?: Record<string, unknown>;
};

const setupMocks = (
  overrides?: Record<string, unknown>,
  hookOverrides?: HookOverrides,
) => {
  mockedUseSystemSettings.mockReturnValue({
    data: { ...baseSettings, ...overrides } as unknown as Settings,
    isLoading: false,
    isRefetching: false,
  });
  mockedUseSettingsMutation.mockReturnValue({
    mutate: vitest.fn(),
    isPending: false,
  });
  mockedUseInstanceName.mockReturnValue("Bazarr");
  mockedUsePlexAuthValidationQuery.mockReturnValue({
    data: {
      valid: false,
      authMethod: "oauth",
    },
    isLoading: false,
    error: null,
    refetch: vitest.fn(),
    ...hookOverrides?.auth,
  });
  mockedUsePlexServersQuery.mockReturnValue({
    data: [],
    error: null,
    refetch: vitest.fn(),
    ...hookOverrides?.servers,
  });
  mockedUsePlexSelectedServerQuery.mockReturnValue({
    data: null,
    ...hookOverrides?.selectedServer,
  });
  mockedUsePlexPinMutation.mockReturnValue({
    mutateAsync: vitest.fn().mockResolvedValue({
      data: { pinId: "123", code: "ABC", authUrl: "http://plex.test/auth" },
    }),
  });
  mockedUsePlexPinCheckQuery.mockReturnValue({
    data: null,
    ...hookOverrides?.pinCheck,
  });
  mockedUsePlexLogoutMutation.mockReturnValue({
    mutate: mockLogoutMutate,
    isPending: false,
  });
  mockedUsePlexServerSelectionMutation.mockReturnValue({
    mutateAsync: mockServerSelectionMutate,
    isPending: false,
  });
  mockedUsePlexLibrariesQuery.mockReturnValue({
    data: [],
    isLoading: false,
    error: null,
    ...hookOverrides?.libraries,
  });
  mockedUsePlexWebhookCreateMutation.mockReturnValue({
    mutateAsync: mockCreateWebhook,
    isPending: false,
  });
  mockedUsePlexWebhookListQuery.mockReturnValue({
    data: null,
    isLoading: false,
    error: null,
    refetch: vitest.fn(),
    ...hookOverrides?.webhooks,
  });
  mockedUsePlexWebhookDeleteMutation.mockReturnValue({
    mutateAsync: mockDeleteWebhook,
    isPending: false,
  });
  mockedUsePlexAutopulseConfigQuery.mockReturnValue({
    data: null,
    refetch: mockRefetchAutopulse,
    isFetching: false,
    ...hookOverrides?.autopulse,
  });
};

const renderPage = async (
  overrides?: Record<string, unknown>,
  hookOverrides?: HookOverrides,
) => {
  setupMocks(overrides, hookOverrides);
  const utils = customRender(<SettingsPlexView />);
  // Flush microtasks from void promises and Mantine Popover transitions
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
  return utils;
};

describe("SettingsPlexView", async () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  beforeAll(() => {
    Element.prototype.scrollIntoView = vitest.fn();
  });

  it("should hide Plex settings when Plex is disabled", async () => {
    await renderPage({
      general: { ...baseSettings.general, use_plex: false },
    });

    expect(
      screen.queryByRole("heading", { name: "Movie Library" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Series Library" }),
    ).not.toBeInTheDocument();
  });

  it("should render Plex settings when Plex is enabled", async () => {
    await renderPage();

    expect(
      screen.getByRole("heading", { name: "Movie Library" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Series Library" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Automation" }),
    ).toBeInTheDocument();
  });

  it("should show Plex OAuth connect state when not authenticated", async () => {
    await renderPage();

    expect(
      screen.getByRole("button", { name: "Connect to Plex" }),
    ).toBeInTheDocument();
  });

  it("should show authenticated Plex state", async () => {
    await renderPage(undefined, {
      auth: {
        data: {
          valid: true,
          authMethod: "oauth",
          username: "testuser",
          email: "test@example.com",
        },
        isLoading: false,
        error: null,
      },
    });

    expect(
      screen.getByText("Connected as testuser (test@example.com)"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Disconnect from Plex" }),
    ).toBeInTheDocument();
  });

  it("should show authentication loading state", async () => {
    await renderPage(undefined, {
      auth: {
        data: undefined,
        isLoading: true,
        error: null,
      },
    });

    expect(
      screen.getByText("Loading authentication status..."),
    ).toBeInTheDocument();
  });

  it("should show server connection status when authenticated", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
    });

    expect(
      screen.getByText("Testing server connections..."),
    ).toBeInTheDocument();
  });

  it("should show a single server without manual selection", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
        ],
        error: null,
      },
    });

    expect(screen.getByText(/My Server/)).toBeInTheDocument();
  });

  it("should show a multiple server selection interface", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
          {
            machineIdentifier: "server-2",
            name: "Other Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://other:32400", local: false },
            connections: [{ uri: "http://other:32400", local: false }],
          },
        ],
        error: null,
      },
    });

    expect(
      screen.getByRole("combobox", { name: "Select server" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Select Server" }),
    ).toBeInTheDocument();
  });

  it("should show library loading alert", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
        ],
        error: null,
      },
      libraries: {
        data: undefined,
        isLoading: true,
        error: null,
      },
    });

    expect(
      screen.getAllByText("Fetching libraries... This might take a moment.")
        .length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should show stale library as unavailable", async () => {
    await renderPage(
      {
        plex: {
          ...baseSettings.plex,
          movie_library: ["Old Library"],
        },
      },
      {
        auth: {
          data: { valid: true, authMethod: "oauth" },
          isLoading: false,
          error: null,
        },
        servers: {
          data: [
            {
              machineIdentifier: "server-1",
              name: "My Server",
              platform: "Plex",
              version: "1.0",
              bestConnection: { uri: "http://localhost:32400", local: true },
              connections: [{ uri: "http://localhost:32400", local: true }],
            },
          ],
          error: null,
        },
        libraries: {
          data: [{ key: "1", title: "Movies", type: "movie", count: 100 }],
          isLoading: false,
          error: null,
        },
      },
    );

    expect(
      screen.getAllByText("Old Library (unavailable)").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should show webhook creation when none exist", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: {
          webhooks: [],
          plexPassSubscription: { hasWebhooksFeature: true },
        },
        isLoading: false,
        error: null,
      },
    });

    expect(screen.getByRole("button", { name: "Add" })).toBeInTheDocument();
    expect(
      screen.getByText("No webhooks found on your Plex server."),
    ).toBeInTheDocument();
  });

  it("should create a webhook", async () => {
    mockCreateWebhook.mockResolvedValueOnce(undefined);

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: {
          webhooks: [],
          plexPassSubscription: { hasWebhooksFeature: true },
        },
        isLoading: false,
        error: null,
      },
    });

    const addButton = screen.getByRole("button", { name: "Add" });

    await userEvent.click(addButton);

    expect(mockCreateWebhook).toHaveBeenCalledTimes(1);
  });

  it("should delete a webhook", async () => {
    mockDeleteWebhook.mockResolvedValueOnce(undefined);

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: {
          webhooks: [
            {
              url: "http://bazarr/api/webhooks/plex?instance=Bazarr",
            },
          ],
          plexPassSubscription: { hasWebhooksFeature: true },
        },
        isLoading: false,
        error: null,
      },
    });

    const removeButton = screen.getByRole("button", { name: "Remove" });

    await userEvent.click(removeButton);

    expect(mockDeleteWebhook).toHaveBeenCalledWith(
      "http://bazarr/api/webhooks/plex?instance=Bazarr",
    );
  });

  it("should generate an autopulse configuration", async () => {
    mockRefetchAutopulse.mockResolvedValueOnce({
      isSuccess: true,
      data: {
        configYaml: "[test]\nkey=value",
        serverName: "My Server",
      },
    });

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      autopulse: {
        data: null,
        refetch: mockRefetchAutopulse,
        isFetching: false,
      },
    });

    const generateButton = screen.getByRole("button", {
      name: "Generate Configuration",
    });

    await userEvent.click(generateButton);

    expect(mockRefetchAutopulse).toHaveBeenCalledTimes(1);
    expect(mockedNotificationsShow).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Success",
        message: "Autopulse configuration generated successfully",
        color: "success",
      }),
    );
  });

  it("should show the OAuth polling state", async () => {
    const windowOpen = vitest.fn();
    Object.defineProperty(window, "open", {
      value: windowOpen,
      configurable: true,
    });

    mockedUsePlexPinMutation.mockReturnValue({
      mutateAsync: vitest.fn().mockResolvedValue({
        data: { pinId: "123", code: "ABC", authUrl: "http://plex.test/auth" },
      }),
    });

    await renderPage(undefined, {
      pinCheck: {
        data: { authenticated: false },
      },
    });

    const connectButton = screen.getByRole("button", {
      name: "Connect to Plex",
    });

    await userEvent.click(connectButton);

    expect(
      screen.getByText(/Complete the authentication in the opened window/i),
    ).toBeInTheDocument();

    Object.defineProperty(window, "open", {
      value: window.open,
      configurable: true,
    });
  });

  it("should disconnect from Plex", async () => {
    await renderPage(undefined, {
      auth: {
        data: {
          valid: true,
          authMethod: "oauth",
          username: "testuser",
          email: "test@example.com",
        },
        isLoading: false,
        error: null,
      },
    });

    const disconnectButton = screen.getByRole("button", {
      name: "Disconnect from Plex",
    });

    await userEvent.click(disconnectButton);

    expect(mockLogoutMutate).toHaveBeenCalledTimes(1);
  });

  it("should show an authentication error", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: false, authMethod: "oauth" },
        isLoading: false,
        error: new Error("Auth failed"),
      },
    });

    expect(screen.getByText("Auth failed")).toBeInTheDocument();
  });

  it("should show a server loading error", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [],
        error: new Error("Servers failed"),
        refetch: vitest.fn(),
      },
    });

    expect(screen.getByText(/Failed to load servers:/i)).toBeInTheDocument();
  });

  it("should select and save a server from the dropdown", async () => {
    mockServerSelectionMutate.mockResolvedValueOnce(undefined);

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
          {
            machineIdentifier: "server-2",
            name: "Other Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://other:32400", local: false },
            connections: [{ uri: "http://other:32400", local: false }],
          },
        ],
        error: null,
      },
    });

    const select = screen.getByRole("combobox", { name: "Select server" });

    await userEvent.click(select);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Other Server (Plex - v1.0)",
    });

    fireEvent.click(option);

    const selectButton = screen.getByRole("button", { name: "Select Server" });

    await userEvent.click(selectButton);

    expect(mockServerSelectionMutate).toHaveBeenCalledTimes(1);
  });

  it("should show a webhook error", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: null,
        isLoading: false,
        error: new Error("Webhook failed"),
      },
    });

    expect(screen.getByText(/Failed to load webhooks:/i)).toBeInTheDocument();
  });

  it("should disable webhook creation without Plex Pass", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: {
          webhooks: [],
          plexPassSubscription: { hasWebhooksFeature: false },
        },
        isLoading: false,
        error: null,
      },
    });

    const addButton = screen.getByRole("button", { name: "Add" });

    expect(addButton).toBeDisabled();
    expect(
      screen.getByText(/Webhooks require a Plex Pass subscription/i),
    ).toBeInTheDocument();
  });

  it("should show an Autopulse 401 error", async () => {
    mockRefetchAutopulse.mockResolvedValueOnce({
      isError: true,
      error: { response: { status: 401 } },
    });

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      autopulse: {
        data: null,
        refetch: mockRefetchAutopulse,
        isFetching: false,
      },
    });

    const generateButton = screen.getByRole("button", {
      name: "Generate Configuration",
    });

    await userEvent.click(generateButton);

    expect(mockedNotificationsShow).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Error",
        message:
          "Plex OAuth authentication required. Please configure OAuth authentication above.",
        color: "danger",
      }),
    );
  });

  it("should complete OAuth when the pin is authenticated", async () => {
    const closeMock = vitest.fn();
    const windowOpen = vitest.fn(
      () => ({ close: closeMock }) as unknown as Window,
    );
    Object.defineProperty(window, "open", {
      value: windowOpen,
      configurable: true,
    });

    mockedUsePlexPinMutation.mockReturnValue({
      mutateAsync: vitest.fn().mockResolvedValue({
        data: { pinId: "123", code: "ABC", authUrl: "http://plex.test/auth" },
      }),
    });

    await renderPage(undefined, {
      pinCheck: {
        data: { authenticated: true },
      },
    });

    const connectButton = screen.getByRole("button", {
      name: "Connect to Plex",
    });

    await userEvent.click(connectButton);

    expect(windowOpen).toHaveBeenCalledTimes(1);
    expect(closeMock).toHaveBeenCalledTimes(1);

    Object.defineProperty(window, "open", {
      value: window.open,
      configurable: true,
    });
  });

  it("should cancel OAuth authentication", async () => {
    const closeMock = vitest.fn();
    const windowOpen = vitest.fn(
      () => ({ close: closeMock }) as unknown as Window,
    );
    Object.defineProperty(window, "open", {
      value: windowOpen,
      configurable: true,
    });

    mockedUsePlexPinMutation.mockReturnValue({
      mutateAsync: vitest.fn().mockResolvedValue({
        data: { pinId: "123", code: "ABC", authUrl: "http://plex.test/auth" },
      }),
    });

    await renderPage(undefined, {
      pinCheck: {
        data: { authenticated: false },
      },
    });

    const connectButton = screen.getByRole("button", {
      name: "Connect to Plex",
    });

    await userEvent.click(connectButton);

    const cancelButton = screen.getByRole("button", { name: "Cancel" });

    await userEvent.click(cancelButton);

    expect(closeMock).toHaveBeenCalledTimes(1);

    Object.defineProperty(window, "open", {
      value: window.open,
      configurable: true,
    });
  });

  it("should show a fallback authentication error message", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: false, authMethod: "oauth" },
        isLoading: false,
        error: new Error(""),
      },
    });

    expect(screen.getByText("Authentication failed")).toBeInTheDocument();
  });

  it("should show a logout success notification", async () => {
    await renderPage(undefined, {
      auth: {
        data: {
          valid: true,
          authMethod: "oauth",
          username: "testuser",
          email: "test@example.com",
        },
        isLoading: false,
        error: null,
      },
    });

    const disconnectButton = screen.getByRole("button", {
      name: "Disconnect from Plex",
    });

    await userEvent.click(disconnectButton);

    expect(mockedNotificationsShow).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Disconnected from Plex",
        message: "All settings related to Plex were removed",
        color: "success",
      }),
    );
  });

  it("should mark a server without a best connection as unavailable", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: null,
            connections: [],
          },
        ],
        error: null,
      },
    });

    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("should initialize the selected server from the saved server", async () => {
    const refetchServers = vitest.fn();

    const { rerender } = await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
        ],
        error: null,
        refetch: refetchServers,
      },
    });

    mockedUsePlexSelectedServerQuery.mockReturnValue({
      data: {
        machineIdentifier: "server-1",
        name: "My Server",
        platform: "Plex",
        version: "1.0",
        bestConnection: { uri: "http://localhost:32400", local: true },
        connections: [{ uri: "http://localhost:32400", local: true }],
      },
    });

    rerender(<SettingsPlexView />);

    expect(
      (await screen.findAllByText(/Connected/i)).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should refresh the server list", async () => {
    const refetchServers = vitest.fn();

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
        ],
        error: null,
        refetch: refetchServers,
      },
    });

    const refreshButton = screen.getByRole("button", {
      name: "Refresh server list",
    });

    await userEvent.click(refreshButton);

    expect(refetchServers).toHaveBeenCalledTimes(1);
  });

  it("should show a webhook loading state", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: null,
        isLoading: true,
        error: null,
      },
    });

    expect(screen.getByRole("combobox", { name: "Webhooks" })).toBeDisabled();
  });

  it("should sort the Bazarr webhook first in the list", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: {
          webhooks: [
            { url: "http://other/plex" },
            { url: "http://bazarr/api/webhooks/plex?instance=Bazarr" },
          ],
          plexPassSubscription: { hasWebhooksFeature: true },
        },
        isLoading: false,
        error: null,
      },
    });

    const select = screen.getByTestId("webhook-select");

    expect(select).toHaveValue(
      "http://bazarr/api/webhooks/plex?instance=Bazarr",
    );
  });

  it("should show an error notification when creating a webhook fails", async () => {
    mockCreateWebhook.mockRejectedValueOnce(new Error("create failed"));

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: {
          webhooks: [],
          plexPassSubscription: { hasWebhooksFeature: true },
        },
        isLoading: false,
        error: null,
      },
    });

    const addButton = screen.getByRole("button", { name: "Add" });

    await userEvent.click(addButton);

    await waitFor(() =>
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Error",
          message: "Failed to create webhook",
          color: "danger",
        }),
      ),
    );
  });

  it("should show an error notification when deleting a webhook fails", async () => {
    mockDeleteWebhook.mockRejectedValueOnce(new Error("delete failed"));

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      webhooks: {
        data: {
          webhooks: [
            {
              url: "http://bazarr/api/webhooks/plex?instance=Bazarr",
            },
          ],
          plexPassSubscription: { hasWebhooksFeature: true },
        },
        isLoading: false,
        error: null,
      },
    });

    const removeButton = screen.getByRole("button", { name: "Remove" });

    await userEvent.click(removeButton);

    await waitFor(() =>
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Error",
          message: "Failed to delete webhook",
          color: "danger",
        }),
      ),
    );
  });

  it("should copy the Autopulse configuration in a secure context", async () => {
    const writeText = vitest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
      writable: true,
    });
    Object.defineProperty(window, "isSecureContext", {
      value: true,
      configurable: true,
    });

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      autopulse: {
        data: {
          configYaml: "[test]\nkey=value",
          serverName: "My Server",
        },
        refetch: mockRefetchAutopulse,
        isFetching: false,
      },
    });

    const copyButton = screen.getByRole("button", {
      name: "Copy configuration",
    });

    await userEvent.click(copyButton);

    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith("[test]\nkey=value"),
    );

    Object.defineProperty(window, "isSecureContext", {
      value: undefined,
      configurable: true,
    });
  });

  it("should warn when copying the Autopulse configuration outside a secure context", async () => {
    Object.defineProperty(window, "isSecureContext", {
      value: false,
      configurable: true,
    });

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      autopulse: {
        data: {
          configYaml: "[test]\nkey=value",
          serverName: "My Server",
        },
        refetch: mockRefetchAutopulse,
        isFetching: false,
      },
    });

    const copyButton = screen.getByRole("button", {
      name: "Copy configuration",
    });

    await userEvent.click(copyButton);

    await waitFor(() =>
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Cannot Copy",
          color: "warning",
        }),
      ),
    );

    Object.defineProperty(window, "isSecureContext", {
      value: undefined,
      configurable: true,
    });
  });

  it("should warn when there is no Autopulse configuration to copy", async () => {
    Object.defineProperty(window, "isSecureContext", {
      value: true,
      configurable: true,
    });

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      autopulse: {
        data: {
          configYaml: "",
          serverName: "My Server",
        },
        refetch: mockRefetchAutopulse,
        isFetching: false,
      },
    });

    const copyButton = screen.getByRole("button", {
      name: "Copy configuration",
    });

    await userEvent.click(copyButton);

    await waitFor(() =>
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Error",
          message: "No configuration to copy",
          color: "danger",
        }),
      ),
    );

    Object.defineProperty(window, "isSecureContext", {
      value: undefined,
      configurable: true,
    });
  });

  it("should show an error when copying the Autopulse configuration fails", async () => {
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: vitest.fn().mockRejectedValue(new Error("copy failed")),
      },
      configurable: true,
      writable: true,
    });
    Object.defineProperty(window, "isSecureContext", {
      value: true,
      configurable: true,
    });

    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      autopulse: {
        data: {
          configYaml: "[test]\nkey=value",
          serverName: "My Server",
        },
        refetch: mockRefetchAutopulse,
        isFetching: false,
      },
    });

    const copyButton = screen.getByRole("button", {
      name: "Copy configuration",
    });

    await userEvent.click(copyButton);

    await waitFor(() =>
      expect(mockedNotificationsShow).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Copy Failed",
          color: "danger",
        }),
      ),
    );

    Object.defineProperty(window, "isSecureContext", {
      value: undefined,
      configurable: true,
    });
  });

  it("should show a library error alert", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
        ],
        error: null,
      },
      libraries: {
        data: undefined,
        isLoading: false,
        error: new Error("library failed"),
      },
    });

    expect(
      screen.getAllByText(
        "Failed to load libraries from Plex. Saved selections shown above.",
      ).length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should show a no libraries alert", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
        ],
        error: null,
      },
      libraries: {
        data: [],
        isLoading: false,
        error: null,
      },
    });

    expect(
      screen.getAllByText("No movie libraries found on your Plex server.")
        .length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should select a Plex library and update its ID", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      servers: {
        data: [
          {
            machineIdentifier: "server-1",
            name: "My Server",
            platform: "Plex",
            version: "1.0",
            bestConnection: { uri: "http://localhost:32400", local: true },
            connections: [{ uri: "http://localhost:32400", local: true }],
          },
        ],
        error: null,
      },
      libraries: {
        data: [
          {
            key: "1",
            title: "Movies",
            type: "movie",
            count: 100,
          },
        ],
        isLoading: false,
        error: null,
      },
    });

    const selects = screen.getAllByRole("combobox");
    const librarySelect = selects[selects.length - 2];

    await userEvent.click(librarySelect);

    const option = screen.getByRole("option", {
      hidden: true,
      name: "Movies (100 items)",
    });

    fireEvent.click(option);

    expect(
      screen.getAllByText("Movies (100 items)").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("should not render a connections card when the selected server is missing", async () => {
    await renderPage(undefined, {
      auth: {
        data: { valid: true, authMethod: "oauth" },
        isLoading: false,
        error: null,
      },
      selectedServer: {
        data: {
          machineIdentifier: "missing-server",
          name: "Missing Server",
          platform: "Plex",
          version: "1.0",
          bestConnection: { uri: "http://localhost:32400", local: true },
          connections: [{ uri: "http://localhost:32400", local: true }],
        },
      },
      servers: {
        data: [],
        error: null,
      },
    });

    expect(screen.queryByText("Verified Connections:")).not.toBeInTheDocument();
  });
});
