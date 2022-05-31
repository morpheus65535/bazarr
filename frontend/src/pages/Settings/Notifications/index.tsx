import { Anchor, Blockquote, Text } from "@mantine/core";
import { FunctionComponent } from "react";
import { Check, Layout, Message, Section } from "../components";
import { NotificationView } from "./components";

const SettingsNotificationsView: FunctionComponent = () => {
  return (
    <Layout name="Notifications">
      <Blockquote>
        <Text>
          Thanks to caronc for his work on{" "}
          <Anchor
            href="https://github.com/caronc/apprise"
            target="_blank"
            rel="noopener noreferrer"
          >
            apprise
          </Anchor>
          , the core of the Bazarr notification system.
        </Text>
        <Text>
          Please follow instructions on his{" "}
          <Anchor
            href="https://github.com/caronc/apprise/wiki"
            target="_blank"
            rel="noopener noreferrer"
          >
            Wiki
          </Anchor>{" "}
          to configure your notification providers.
        </Text>
      </Blockquote>
      <Section header="Notifications">
        <NotificationView></NotificationView>
      </Section>
      <Section header="Options">
        <Check
          label="Silent for Manual Actions"
          settingKey="settings-general-dont_notify_manual_actions"
        ></Check>
        <Message>
          Suppress notifications when manually download/upload subtitles.
        </Message>
      </Section>
    </Layout>
  );
};

export default SettingsNotificationsView;
