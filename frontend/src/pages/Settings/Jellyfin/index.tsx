import {
  FunctionComponent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Badge,
  Button,
  Group,
  Select,
  Stack,
  Text as MantineText,
} from "@mantine/core";
import { get } from "lodash";
import { useJellyfinTestConnectionMutation } from "@/apis/hooks/jellyfin";
import { JellyfinTestResult } from "@/apis/raw/jellyfin";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Password,
  Section,
  Text,
} from "@/pages/Settings/components";
import { jellyfinEnabledKey } from "@/pages/Settings/keys";
import {
  BaseInput,
  useBaseInput,
  useSettingValue,
} from "@/pages/Settings/utilities/hooks";
import { useSettings } from "@/pages/Settings/utilities/useSettings";
import LibrarySelector from "./LibrarySelector";

const refreshMethodOptions = [
  {
    value: "immediate",
    label: "Immediate",
    description:
      "Re-read item metadata right away without contacting external providers. Recommended for most setups.",
  },
  {
    value: "async",
    label: "Async",
    description:
      "Notify Jellyfin of a filesystem change. Jellyfin picks it up in the background after ~30-60 seconds.",
  },
];

const RefreshMethodSelector: FunctionComponent = () => {
  const { value, update } = useBaseInput<BaseInput<string>, string>({
    settingKey: "settings-jellyfin-refresh_method",
  });

  const selected =
    refreshMethodOptions.find((o) => o.value === value) ??
    refreshMethodOptions[0];

  return (
    <>
      <Select
        label="How to notify Jellyfin after subtitle changes"
        data={refreshMethodOptions}
        value={value ?? "immediate"}
        onChange={(v) => update(v)}
        renderOption={({ option }) => {
          const item = refreshMethodOptions.find(
            (o) => o.value === option.value,
          );
          return (
            <Stack gap={1}>
              <MantineText size="sm" fw={500}>
                {item?.label}
              </MantineText>
              <MantineText size="xs" c="dimmed">
                {item?.description}
              </MantineText>
            </Stack>
          );
        }}
      />
      {selected && <Message>{selected.description}</Message>}
    </>
  );
};

interface ConnectionStatus {
  result: JellyfinTestResult | null;
  isConfigured: boolean;
  isConnected: boolean;
  isTesting: boolean;
  testConnection: () => void;
}

const useJellyfinConnectionStatus = (): ConnectionStatus => {
  const settings = useSettings();

  const jellyfinUrl = useSettingValue<string>("settings-jellyfin-url");
  const jellyfinApikey = useSettingValue<string>("settings-jellyfin-apikey");
  const mutation = useJellyfinTestConnectionMutation();

  const liveKey = `${jellyfinUrl ?? ""}|${jellyfinApikey ?? ""}`;
  const isConfigured = Boolean(jellyfinUrl && jellyfinApikey);

  // Remember which credentials the current result was produced for, so the
  // gate expires as soon as the form values change.
  const [tested, setTested] = useState<{
    key: string;
    result: JellyfinTestResult;
  } | null>(null);

  const runTest = useCallback(
    (url: string, apikey: string) => {
      mutation.mutate(
        { url, apikey },
        {
          onSuccess: (data) =>
            setTested({ key: `${url}|${apikey}`, result: data }),
          onError: () =>
            setTested({
              key: `${url}|${apikey}`,
              result: { success: false, error: "Connection failed" },
            }),
        },
      );
    },
    [mutation],
  );

  const testConnection = useCallback(() => {
    if (!jellyfinUrl || !jellyfinApikey) return;
    runTest(jellyfinUrl, jellyfinApikey);
  }, [jellyfinUrl, jellyfinApikey, runTest]);

  // Re-validate the *saved* credentials once on load so the connection state
  // survives a page refresh (same auto-fetch pattern the Plex page uses).
  const savedUrl = get(settings, "jellyfin.url", null) as string | null;
  const savedApikey = get(settings, "jellyfin.apikey", null) as string | null;
  const autoTestedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!savedUrl || !savedApikey) return;
    const key = `${savedUrl}|${savedApikey}`;
    if (autoTestedRef.current !== key) {
      autoTestedRef.current = key;
      runTest(savedUrl, savedApikey);
    }
  }, [savedUrl, savedApikey, runTest]);

  // Only treat the connection as verified when the latest test ran against
  // the credentials currently in the form (stale success doesn't gate).
  const isConnected = Boolean(tested?.result.success && tested.key === liveKey);

  return {
    result: tested?.result ?? null,
    isConfigured,
    isConnected,
    isTesting: mutation.isPending,
    testConnection,
  };
};

const SettingsJellyfinContent: FunctionComponent = () => {
  const { result, isConfigured, isConnected, isTesting, testConnection } =
    useJellyfinConnectionStatus();

  return (
    <>
      <Section header="Use Jellyfin Media Server">
        <Check label="Enabled" settingKey={jellyfinEnabledKey} />
      </Section>

      <CollapseBox settingKey={jellyfinEnabledKey}>
        <Section header="Connection">
          <Stack gap="xs">
            <Text
              label="Server URL"
              settingKey="settings-jellyfin-url"
              placeholder="http://localhost:8096"
              description="Full URL of your Jellyfin server (e.g., http://192.168.1.100:8096)"
            />
            <Password
              label="API Key"
              settingKey="settings-jellyfin-apikey"
              placeholder="Enter your Jellyfin API key"
              description="Generate an API key in Jellyfin Dashboard > API Keys"
            />
            <RefreshMethodSelector />
            <Group gap="xs" align="center" wrap="wrap">
              <Button
                variant="light"
                color="secondary"
                loading={isTesting}
                disabled={!isConfigured}
                onClick={testConnection}
              >
                Test Connection
              </Button>
              {result && !isTesting && (
                <>
                  {result.success ? (
                    <>
                      <Badge color="success" size="sm">
                        Connected
                      </Badge>
                      <MantineText size="sm" c="dimmed">
                        {result.serverName} (v{result.version})
                      </MantineText>
                    </>
                  ) : (
                    <MantineText size="sm" c="danger">
                      {result.error || "Connection failed"}
                    </MantineText>
                  )}
                </>
              )}
            </Group>
            {!isConfigured && (
              <Message type="warning">
                Enter your Jellyfin server URL and API key to test the
                connection.
              </Message>
            )}
          </Stack>
        </Section>

        {isConnected && (
          <>
            <Section header="Movie Library">
              <LibrarySelector
                label="Library Name"
                settingKey="settings-jellyfin-movie_library"
                settingKeyIds="settings-jellyfin-movie_library_ids"
                libraryType="movies"
                description="Select your movie library from Jellyfin"
              />
              <Check
                label="Refresh movie metadata after downloading subtitles"
                settingKey="settings-jellyfin-update_movie_library"
              />
            </Section>

            <Section header="Series Library">
              <LibrarySelector
                label="Library Name"
                settingKey="settings-jellyfin-series_library"
                settingKeyIds="settings-jellyfin-series_library_ids"
                libraryType="tvshows"
                description="Select your TV show library from Jellyfin"
              />
              <Check
                label="Refresh series metadata after downloading subtitles"
                settingKey="settings-jellyfin-update_series_library"
              />
            </Section>
          </>
        )}
      </CollapseBox>
    </>
  );
};

const SettingsJellyfinView: FunctionComponent = () => {
  return (
    <Layout name="Jellyfin">
      <SettingsJellyfinContent />
    </Layout>
  );
};

export default SettingsJellyfinView;
