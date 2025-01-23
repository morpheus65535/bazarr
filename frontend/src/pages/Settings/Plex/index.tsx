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
      <Section header="Use Plex integration">
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
        <Section header="Movie editing">
          <Text
            label="Name of the library"
            settingKey="settings-plex-movie_library"
          ></Text>
          <Check
            label="Set the movie as recently added after downloading the subtitles"
            settingKey="settings-plex-set_added"
          ></Check>
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsPlexView;
