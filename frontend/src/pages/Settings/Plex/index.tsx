import { Box, Button, Collapse, Group, Paper, Stack } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { faChevronDown, faChevronUp } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
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
import { PlexSettings } from "./PlexSettings";

const SettingsPlexView = () => {
  const [manualConfigOpen, { toggle: manualConfigToggle }] =
    useDisclosure(false);

  return (
    <Layout name="Interface">
      <Section header="Use Plex Media Server">
        <Check label="Enabled" settingKey={plexEnabledKey} />
      </Section>

      <CollapseBox settingKey={plexEnabledKey}>
        <Paper p="xl" radius="md">
          <Stack gap="lg">
            {/* OAuth Section - Prominent */}
            <Box>
              <PlexSettings />
            </Box>

            {/* Manual Configuration - Collapsible */}
            <Box>
              <Button
                variant="subtle"
                color="gray"
                size="md"
                leftSection={
                  manualConfigOpen ? (
                    <FontAwesomeIcon icon={faChevronUp} size="sm" />
                  ) : (
                    <FontAwesomeIcon icon={faChevronDown} size="sm" />
                  )
                }
                onClick={manualConfigToggle}
              >
                Manual Configuration (Legacy)
              </Button>

              <Collapse in={manualConfigOpen}>
                <Paper p="lg" mt="sm" radius="md" withBorder>
                  <Stack gap="md">
                    <Message>
                      This legacy manual configuration is not needed when using
                      Plex OAuth above. Use this only if OAuth is not available
                      or preferred.
                    </Message>

                    <Group grow>
                      <Text
                        label="Server Address"
                        settingKey="settings-plex-ip"
                      />
                      <Number
                        label="Port"
                        settingKey="settings-plex-port"
                        defaultValue={32400}
                      />
                    </Group>

                    <Text
                      label="API Token"
                      settingKey="settings-plex-apikey"
                      placeholder="Enter your Plex API token"
                    />

                    <Check
                      label="Use SSL/HTTPS connection"
                      settingKey="settings-plex-ssl"
                    />

                    <Message>
                      To get your API token, visit: https://app.plex.tv/web/app
                      → Settings → Account → Privacy → Show API Token
                    </Message>
                  </Stack>
                </Paper>
              </Collapse>
            </Box>
          </Stack>
        </Paper>

        {/* Plex Library Configuration */}
        <Section header="Movie Library">
          <Text
            label="Library Name"
            settingKey="settings-plex-movie_library"
            placeholder="Movies"
          />
          <Check
            label="Mark movies as recently added after downloading subtitles"
            settingKey="settings-plex-set_movie_added"
          />
          <Check
            label="Update movie library after downloading subtitles"
            settingKey="settings-plex-update_movie_library"
          />
        </Section>

        <Section header="Series Library">
          <Text
            label="Library Name"
            settingKey="settings-plex-series_library"
            placeholder="TV Shows"
          />
          <Check
            label="Mark episodes as recently added after downloading subtitles"
            settingKey="settings-plex-set_episode_added"
          />
          <Check
            label="Update series library after downloading subtitles"
            settingKey="settings-plex-update_series_library"
          />
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
