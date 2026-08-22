import { FunctionComponent } from "react";
import { Link } from "react-router";
import { Button, Code, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useSystemWebhookTestMutation } from "@/apis/hooks/system";
import {
  Check,
  CollapseBox,
  Message,
  Password,
  Text as SettingsText,
} from "@/pages/Settings/components";

const ExternalWebhookSelector: FunctionComponent = () => {
  const testMutation = useSystemWebhookTestMutation();

  const handleTestConnection = async () => {
    try {
      const result = await testMutation.mutateAsync();
      notifications.show({
        title: result.data.success ? "Success" : "Error",
        message: result.data.message,
        color: result.data.success ? "success" : "danger",
      });
    } catch {
      notifications.show({
        title: "Error",
        message: "Failed to test external webhook connection",
        color: "danger",
      });
    }
  };

  return (
    <>
      <Message>
        Send webhook notifications to external services when subtitles are
        downloaded. For Autopulse auto-configuration with Plex OAuth, see the{" "}
        <Text component={Link} to="/settings/plex" fw={500} c="info" td="none">
          Plex settings section
        </Text>
        .
      </Message>
      <Check
        label="Enable external webhook after subtitle download"
        settingKey="settings-general-use_external_webhook"
      />
      <CollapseBox indent settingKey="settings-general-use_external_webhook">
        <SettingsText
          label="Webhook URL"
          settingKey="settings-general-external_webhook_url"
          placeholder="http://localhost:2875/triggers/bazarr"
        />
        <Message>
          Examples:
          <br />• Autopulse (local):{" "}
          <Code>http://localhost:2875/triggers/bazarr</Code>
          <br />• Autopulse (network):{" "}
          <Code>http://192.168.1.100:2875/triggers/bazarr</Code>
          <br />• Autopulse (Docker):{" "}
          <Code>http://autopulse:2875/triggers/bazarr</Code>
          <br />• Custom webhook: <Code>http://your-server:8080/webhook</Code>
        </Message>
        <SettingsText
          label="Username (optional)"
          settingKey="settings-general-external_webhook_username"
          placeholder="admin"
        />
        <Password
          label="Password (optional)"
          settingKey="settings-general-external_webhook_password"
        />
        <Button onClick={handleTestConnection} loading={testMutation.isPending}>
          Test Connection
        </Button>
      </CollapseBox>
    </>
  );
};

export default ExternalWebhookSelector;
