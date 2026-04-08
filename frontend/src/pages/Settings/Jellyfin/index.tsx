import { FunctionComponent, useCallback, useState } from "react";
import { Button, Select, Stack, Text as MantineText } from "@mantine/core";
import { useJellyfinTestConnectionMutation } from "@/apis/hooks/jellyfin";
import {
  Check,
  CollapseBox,
  Layout,
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
import LibrarySelector from "./LibrarySelector";

const JellyfinTestButton: FunctionComponent = () => {
  const [title, setTitle] = useState("Test");
  const [color, setColor] = useState("primary");
  const mutation = useJellyfinTestConnectionMutation();

  const jellyfinUrl = useSettingValue<string>("settings-jellyfin-url");
  const jellyfinApikey = useSettingValue<string>("settings-jellyfin-apikey");

  const click = useCallback(() => {
    if (!jellyfinUrl || !jellyfinApikey) {
      setTitle("URL and API Key required");
      setColor("danger");
      return;
    }

    setTitle("Testing...");
    setColor("primary");

    mutation.mutate(
      { url: jellyfinUrl, apikey: jellyfinApikey },
      {
        onSuccess: (data) => {
          if (data.success) {
            setTitle(`${data.server_name} (v${data.version})`);
            setColor("success");
          } else {
            setTitle(data.error || "Connection failed");
            setColor("danger");
          }
        },
        onError: () => {
          setTitle("Connection failed");
          setColor("danger");
        },
      },
    );
  }, [jellyfinUrl, jellyfinApikey, mutation]);

  return (
    <Button autoContrast onClick={click} variant={color}>
      {title}
    </Button>
  );
};

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

  return (
    <Select
      label="How to notify Jellyfin after subtitle changes"
      data={refreshMethodOptions}
      value={value ?? "immediate"}
      onChange={(v) => update(v)}
      renderOption={({ option }) => {
        const item = refreshMethodOptions.find((o) => o.value === option.value);
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
  );
};

const SettingsJellyfinView: FunctionComponent = () => {
  return (
    <Layout name="Interface">
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
            <JellyfinTestButton />
          </Stack>
        </Section>

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
      </CollapseBox>
    </Layout>
  );
};

export default SettingsJellyfinView;
