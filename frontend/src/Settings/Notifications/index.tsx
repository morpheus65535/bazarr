import React, { FunctionComponent } from "react";
import { Alert } from "react-bootstrap";
import { Check, Group, Input, Message, SettingsProvider } from "../components";
import { NotificationView } from "./components";

const SettingsNotificationsView: FunctionComponent = () => {
  return (
    <SettingsProvider title="Notifications - Bazarr (Settings)">
      <Alert variant="secondary">
        Thanks to caronc for his work on{" "}
        <a
          href="https://github.com/caronc/apprise"
          target="_blank"
          rel="noopener noreferrer"
        >
          apprise
        </a>
        , the core of the Bazarr notification system.
      </Alert>
      <Alert variant="secondary">
        Please follow instructions on his{" "}
        <a
          href="https://github.com/caronc/apprise/wiki"
          target="_blank"
          rel="noopener noreferrer"
        >
          Wiki
        </a>{" "}
        to configure your notification providers.
      </Alert>
      <Group header="Notifications">
        <NotificationView></NotificationView>
      </Group>
      <Group header="Options">
        <Input>
          <Check
            label="Slient for Manual Actions"
            settingKey="settings-general-dont_notify_manual_actions"
          ></Check>
          <Message>
            Suppress notifications when manually download/upload subtitles.
          </Message>
        </Input>
      </Group>
    </SettingsProvider>
  );
};

export default SettingsNotificationsView;
