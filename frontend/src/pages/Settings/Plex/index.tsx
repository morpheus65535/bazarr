import { Link } from "react-router";
import { Code, Text } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexServersQuery,
} from "@/apis/hooks/plex";
import {
  Check,
  CollapseBox,
  Layout,
  Message,
  Section,
} from "@/pages/Settings/components";
import { plexEnabledKey } from "@/pages/Settings/keys";
import AuthSection from "./AuthSection";
import AutopulseSelector from "./AutopulseSelector";
import LibrarySelector from "./LibrarySelector";
import ServerSection from "./ServerSection";
import WebhookSelector from "./WebhookSelector";

const SettingsPlexView = () => {
  // Progressive disclosure (the same pattern ServerSection uses): library
  // settings only apply once Plex is connected, and they need a reachable
  // server on top of that. Webhooks live on the plex.tv account, so they
  // only need authentication.
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.authMethod === "oauth",
  );
  const { data: servers = [] } = usePlexServersQuery();
  const hasServer = servers.some(
    (server: Plex.Server) => server.bestConnection,
  );

  return (
    <Layout name="Interface">
      <Section header="Use Plex Media Server">
        <Check label="Enabled" settingKey={plexEnabledKey} />
      </Section>

      <CollapseBox settingKey={plexEnabledKey}>
        <Section header="Connection">
          <AuthSection />
        </Section>

        {isAuthenticated && (
          <Section header="Server">
            <ServerSection />
          </Section>
        )}

        {isAuthenticated && hasServer && (
          <>
            <Section header="Movie Library">
              <LibrarySelector
                label="Library Name"
                settingKey="settings-plex-movie_library"
                settingKeyIds="settings-plex-movie_library_ids"
                libraryType="movie"
                description="Select your movie library from Plex"
              />
              <Check
                label="Mark movies as recently added after downloading subtitles"
                settingKey="settings-plex-set_movie_added"
              />
              <Message>
                Updates the movie's added date in Plex so it appears in the
                Recently Added hub.
              </Message>
              <Check
                label="Refresh movie metadata after downloading subtitles (recommended)"
                settingKey="settings-plex-update_movie_library"
              />
              <Message>
                Refreshes the movie in Plex so the newly downloaded subtitle
                file is detected.
              </Message>
            </Section>

            <Section header="Series Library">
              <LibrarySelector
                label="Library Name"
                settingKey="settings-plex-series_library"
                settingKeyIds="settings-plex-series_library_ids"
                libraryType="show"
                description="Select your TV show library from Plex"
              />
              <Check
                label="Mark episodes as recently added after downloading subtitles"
                settingKey="settings-plex-set_episode_added"
              />
              <Message>
                Updates the episode's added date in Plex so it appears in the
                Recently Added hub.
              </Message>
              <Check
                label="Refresh series metadata after downloading subtitles (recommended)"
                settingKey="settings-plex-update_series_library"
              />
              <Message>
                Refreshes the episode in Plex so the newly downloaded subtitle
                file is detected.
              </Message>
            </Section>
          </>
        )}

        {isAuthenticated && (
          <Section header="Automation">
            <WebhookSelector
              label="Webhooks"
              description="Create a Bazarr webhook in Plex to automatically search for subtitles when content starts playing. Manage and remove existing webhooks for convenience."
            />
            {hasServer && (
              <AutopulseSelector
                label="Autopulse Configuration"
                description={
                  <>
                    Generate a ready-to-use Autopulse configuration tailored to
                    your Plex server. Includes optimized settings, OAuth
                    authentication, and automatic path rewrite detection. Deploy
                    as <Code>config.toml</Code> to your Autopulse data directory
                    for a new setup, or copy specific sections to extend your
                    existing configuration.
                    <br />
                    <br />
                    To enable the webhook trigger, see the{" "}
                    <Text
                      component={Link}
                      to="/settings/general"
                      fw={500}
                      c="info"
                      td="none"
                    >
                      External Integrations section
                    </Text>
                    .
                  </>
                }
              />
            )}
          </Section>
        )}
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
