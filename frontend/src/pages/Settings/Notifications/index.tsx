import { Alert, Anchor } from "@mantine/core";
import { FunctionComponent } from "react";
import { Check, Group, Input, Layout, Message } from "../components";
import { NotificationView } from "./components";

const SettingsNotificationsView: FunctionComponent = () => {
  return (
    <Layout name="Notifications">
      <Alert color="secondary">
        Thanks to caronc for his work on
        <Anchor
          href="https://github.com/caronc/apprise"
          target="_blank"
          rel="noopener noreferrer"
        >
          apprise
        </Anchor>
        , the core of the Bazarr notification system.
      </Alert>
      <Alert color="secondary">
        Please follow instructions on his
        <Anchor
          href="https://github.com/caronc/apprise/wiki"
          target="_blank"
          rel="noopener noreferrer"
        >
          Wiki
        </Anchor>
        to configure your notification providers.
      </Alert>
      <Group header="Notifications">
        <NotificationView></NotificationView>
      </Group>
      <Group header="Options">
        <Input>
          <Check
            label="Silent for Manual Actions"
            settingKey="settings-general-dont_notify_manual_actions"
          ></Check>
          <Message>
            Suppress notifications when manually download/upload subtitles.
          </Message>
        </Input>
      </Group>
    </Layout>
  );
};

export default SettingsNotificationsView;
