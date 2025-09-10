import { Box, Paper } from "@mantine/core";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Number,
  Password,
  Section,
  Text,
} from "@/pages/Settings/components";
import { plexEnabledKey } from "@/pages/Settings/keys";
import AutopulseSelector from "./AutopulseSelector";
import LibrarySelector from "./LibrarySelector";
import PlexSettings from "./PlexSettings";
import WebhookSelector from "./WebhookSelector";

const SettingsPlexView = () => {
  return (
    <Layout name="Interface">
      <Section header="Use Plex Media Server">
        <Check label="Enabled" settingKey={plexEnabledKey} />
      </Section>

      <CollapseBox settingKey={plexEnabledKey}>
        <Paper p="xl" radius="md">
          <Box>
            <PlexSettings />
          </Box>
        </Paper>

        {/* Plex Library Configuration */}
        <Section header="Movie Library">
          <LibrarySelector
            label="Library Name"
            settingKey="settings-plex-movie_library"
            libraryType="movie"
            placeholder="Movies"
            description="Select your movie library from Plex"
          />
          <Check
            label="Mark movies as recently added after downloading subtitles"
            settingKey="settings-plex-set_movie_added"
          />
          <Check
            label="Refresh movie metadata after downloading subtitles (recommended)"
            settingKey="settings-plex-update_movie_library"
          />
        </Section>

        <Section header="Series Library">
          <LibrarySelector
            label="Library Name"
            settingKey="settings-plex-series_library"
            libraryType="show"
            placeholder="TV Shows"
            description="Select your TV show library from Plex"
          />
          <Check
            label="Mark episodes as recently added after downloading subtitles"
            settingKey="settings-plex-set_episode_added"
          />
          <Check
            label="Refresh series metadata after downloading subtitles (recommended)"
            settingKey="settings-plex-update_series_library"
          />
        </Section>

        <Section header="Automation">
          <WebhookSelector
            label="Webhooks"
            description="Create a Bazarr webhook in Plex to automatically search for subtitles when content starts playing. Manage and remove existing webhooks for convenience."
          />
        </Section>

        <Section header="Autopulse Integration">
          <AutopulseSelector
            label="Test Autopulse Connection"
            description="Verify that Bazarr can connect to your Autopulse instance"
          />
          <Message>
            Automatically trigger Autopulse when subtitles are downloaded to
            refresh Plex metadata. Autopulse must be configured with a "manual"
            trigger.
          </Message>
          <CollapseBox indent settingKey="settings-plex-use_autopulse">
            <Text
              label="Autopulse Host"
              settingKey="settings-plex-autopulse_host"
              placeholder="autopulse or 192.168.1.100"
            />
            <Number
              label="Autopulse Port"
              settingKey="settings-plex-autopulse_port"
            />
            <Text
              label="Username (optional)"
              settingKey="settings-plex-autopulse_username"
              placeholder="admin"
            />
            <Password
              label="Password (optional)"
              settingKey="settings-plex-autopulse_password"
            />
            <Message>
              How it works: When Bazarr downloads subtitles, it automatically
              calls Autopulse's manual trigger endpoint (GET
              http://your-host:2875/triggers/manual?path=/media/path). Autopulse
              will then trigger the appropriate Plex library refresh for that
              path. No manual webhook configuration required!
            </Message>
          </CollapseBox>
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
