import { Box, Paper } from "@mantine/core";
import {
  Check,
  CollapseBox,
  Layout,
  Section,
} from "@/pages/Settings/components";
import { plexEnabledKey } from "@/pages/Settings/keys";
import LibrarySelector from "./LibrarySelector";
import PlexSettings from "./PlexSettings";

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
            label="Update movie library after downloading subtitles"
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
            label="Update series library after downloading subtitles"
            settingKey="settings-plex-update_series_library"
          />
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
