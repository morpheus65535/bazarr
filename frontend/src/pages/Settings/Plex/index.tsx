import { Box, Paper } from "@mantine/core";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Password,
  Section,
  Text,
} from "@/pages/Settings/components";
import { plexEnabledKey } from "@/pages/Settings/keys";
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

        <Section header="External Webhooks">
          <Check
            label="Call external webhook after subtitle download"
            settingKey="settings-plex-use_subtitle_webhook"
          />
          <Message>
            Send HTTP request to external service (like Autopulse) after
            downloading subtitles to trigger Plex metadata refresh.
          </Message>
          <CollapseBox indent settingKey="settings-plex-use_subtitle_webhook">
            <Text
              label="Webhook URL"
              settingKey="settings-plex-subtitle_webhook_url"
              placeholder="http://autopulse:2875/triggers/bazarr-trigger"
            />
            <Text
              label="Username (optional)"
              settingKey="settings-plex-subtitle_webhook_username"
              placeholder="admin"
            />
            <Password
              label="Password (optional)"
              settingKey="settings-plex-subtitle_webhook_password"
            />
            <Message>
              <strong>Autopulse Example:</strong>
              <br />
              URL: http://autopulse:2875/triggers/bazarr-hd
              <br />
              Username: admin
              <br />
              Password: your-autopulse-password
              <br />
              <br />
              The media file path will be automatically appended as a "path"
              query parameter. See Bazarr documentation for complete Autopulse
              setup instructions.
            </Message>
          </CollapseBox>
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
