// eslint-disable-next-line simple-import-sort/imports
import { FunctionComponent } from "react";
import { Anchor, Blockquote, Text } from "@mantine/core";
import { Check, Layout, Message, Section } from "@/pages/Settings/components";
import { NotificationView } from "./components";
import { faQuoteLeftAlt } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

const SettingsNotificationsView: FunctionComponent = () => {
  return (
    <Layout name="Notifications">
      <Blockquote
        bg="transparent"
        mt="xl"
        icon={<FontAwesomeIcon icon={faQuoteLeftAlt}></FontAwesomeIcon>}
      >
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
