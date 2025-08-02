import { FunctionComponent } from "react";
import { Button, Select } from "@mantine/core";
import {
  usePlexOAuth,
  usePlexSelectServer,
  usePlexServers,
} from "@/apis/hooks";
import { PlexServer } from "@/apis/raw/plex";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Number,
  Section,
  Text,
} from "@/pages/Settings/components";
import { plexEnabledKey } from "@/pages/Settings/keys";

const SettingsPlexView: FunctionComponent = () => {
  const { data: serversData, isLoading, error } = usePlexServers();
  const oauthMutation = usePlexOAuth();
  const selectServerMutation = usePlexSelectServer();

  const authenticated = !error && serversData?.servers;
  const servers = serversData?.servers || [];

  const handleAuthenticate = async () => {
    try {
      const result = await oauthMutation.mutateAsync();
      if (result.redirect_url) {
        window.location.href = result.redirect_url;
      }
    } catch {
      // Authentication failed - error is handled by the UI
    }
  };

  const handleSelectServer = (value: string | null) => {
    if (!value || !servers) return;

    const serverIndex = parseInt(value, 10);
    const server = servers[serverIndex];

    if (server) {
      selectServerMutation.mutate({
        address: server.address,
        port: server.port,
        ssl: server.ssl,
      });
    }
  };

  const serverOptions = servers.map((srv: PlexServer, idx: number) => ({
    value: idx.toString(),
    label: `${srv.name} (${srv.address}:${srv.port})`,
  }));

  return (
    <Layout name="Interface">
      <Section header="Use Plex operations">
        <Check label="Enabled" settingKey={plexEnabledKey}></Check>

        {!authenticated ? (
          <Button
            onClick={handleAuthenticate}
            loading={oauthMutation.isPending}
            disabled={isLoading}
          >
            Authenticate with Plex.tv
          </Button>
        ) : (
          <Select
            label="Select Plex Server"
            placeholder="-- Select --"
            data={serverOptions}
            onChange={handleSelectServer}
            disabled={selectServerMutation.isPending}
          />
        )}

        {error && (
          <Message>
            Failed to connect to Plex. Please authenticate first.
          </Message>
        )}
      </Section>
      <CollapseBox settingKey={plexEnabledKey}>
        <Section header="Host">
          <Text label="Address" settingKey="settings-plex-ip"></Text>
          <Number
            label="Port"
            settingKey="settings-plex-port"
            defaultValue={32400}
          ></Number>
          <Message>Hostname or IPv4 Address</Message>
          <Text label="API Token" settingKey="settings-plex-apikey"></Text>
          <Check label="SSL" settingKey="settings-plex-ssl"></Check>
        </Section>
        <Section header="Movie library">
          <Text
            label="Name of the library"
            settingKey="settings-plex-movie_library"
          ></Text>
          <Check
            label="Mark the movie as recently added after downloading subtitles"
            settingKey="settings-plex-set_movie_added"
          ></Check>
          <Check
            label="Scan library for new files after downloading subtitles"
            settingKey="settings-plex-update_movie_library"
          ></Check>
          <Message>Can be helpful for remote media files</Message>
        </Section>
        <Section header="Series library">
          <Text
            label="Name of the library"
            settingKey="settings-plex-series_library"
          ></Text>
          <Check
            label="Mark the episode as recently added after downloading subtitles"
            settingKey="settings-plex-set_episode_added"
          ></Check>
          <Check
            label="Scan library for new files after downloading subtitles"
            settingKey="settings-plex-update_series_library"
          ></Check>
          <Message>Can be helpful for remote media files</Message>
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
