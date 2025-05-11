import { FunctionComponent } from "react";
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
  return (
    <Layout name="Interface">
      <Section header="Use Plex operations">
        <Check label="Enabled" settingKey={plexEnabledKey}></Check>
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
