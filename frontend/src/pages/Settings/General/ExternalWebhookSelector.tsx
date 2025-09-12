import { FunctionComponent } from "react";
import { Link } from "react-router";
import { Button, Code, Group, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useSystemWebhookTestMutation } from "@/apis/hooks/system";
import {
  Check,
  CollapseBox,
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
        color: result.data.success ? "green" : "red",
      });
    } catch (error) {
      notifications.show({
        title: "Error",
        message: "Failed to test external webhook connection",
        color: "red",
      });
    }
  };

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        Send webhook notifications to external services when subtitles are
        downloaded. For Autopulse auto-configuration with Plex OAuth, see the{" "}
        <Text component={Link} to="/settings/plex" fw={500} c="blue" td="none">
          Plex settings section
        </Text>
        .
      </Text>

      <Check
        label="Enable external webhook after subtitle download"
        settingKey="settings-general-use_autopulse"
      />

      <CollapseBox indent settingKey="settings-general-use_autopulse">
        <Stack gap="md">
          <Text fw={500}>Generic Webhook Configuration</Text>
          <SettingsText
            label="Webhook URL"
            settingKey="settings-general-autopulse_url"
            placeholder="http://localhost:2875/triggers/manual"
          />
          <Text size="xs" c="dimmed" mt="-xs" mb="sm">
            Examples:
            <br />• Autopulse (local):{" "}
            <Code>http://localhost:2875/triggers/manual</Code>
            <br />• Autopulse (network):{" "}
            <Code>http://192.168.1.100:2875/triggers/manual</Code>
            <br />• Autopulse (Docker):{" "}
            <Code>http://autopulse:2875/triggers/manual</Code>
            <br />• Custom webhook: <Code>http://your-server:8080/webhook</Code>
          </Text>
          <SettingsText
            label="Username (optional)"
            settingKey="settings-general-autopulse_username"
            placeholder="admin"
          />
          <Password
            label="Password (optional)"
            settingKey="settings-general-autopulse_password"
          />

          <Group gap="sm">
            <Button
              onClick={handleTestConnection}
              loading={testMutation.isPending}
              size="sm"
              variant="light"
            >
              Test Connection
            </Button>
          </Group>
        </Stack>
      </CollapseBox>
    </Stack>
  );
};

export default ExternalWebhookSelector;
