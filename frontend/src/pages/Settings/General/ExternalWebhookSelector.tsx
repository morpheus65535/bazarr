import { FunctionComponent } from "react";
import { Alert, Button, Card, Group, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  usePlexAuthValidationQuery,
  usePlexAutopulseConfigQuery,
  usePlexAutopulseTestMutation,
} from "@/apis/hooks/plex";
import {
  Check,
  CollapseBox,
  Number,
  Password,
  Text as SettingsText,
} from "@/pages/Settings/components";

const ExternalWebhookSelector: FunctionComponent = () => {
  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isPlexAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  const testMutation = usePlexAutopulseTestMutation();

  const {
    data: plexConfigData,
    refetch: refetchPlexConfig,
    isFetching: isFetchingPlexConfig,
  } = usePlexAutopulseConfigQuery({
    enabled: false,
    staleTime: Infinity,
    gcTime: Infinity,
  });

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

  const handleGetPlexConfig = async () => {
    try {
      const result = await refetchPlexConfig();
      if (result.data) {
        notifications.show({
          title: "Success",
          message: `Plex config available: ${result.data.server_name || "Server"}`,
          color: "green",
        });
      } else {
        notifications.show({
          title: "Error",
          message: "Failed to get Plex configuration",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: "Failed to get Plex configuration",
        color: "red",
      });
    }
  };

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        Send webhook notifications to external services when subtitles are
        downloaded. Supports generic webhooks and auto-configuration for
        Autopulse.
      </Text>

      <Check
        label="Enable external webhook after subtitle download"
        settingKey="settings-general-use_external_webhook"
      />

      <CollapseBox indent settingKey="settings-general-use_external_webhook">
        <Stack gap="md">
          <Text fw={500}>Generic Webhook Configuration</Text>
          <SettingsText
            label="Webhook URL"
            settingKey="settings-general-external_webhook_url"
            placeholder="http://localhost:8080/webhook or http://autopulse:2875/triggers/manual"
          />
          <SettingsText
            label="Username (optional)"
            settingKey="settings-general-external_webhook_username"
            placeholder="admin"
          />
          <Password
            label="Password (optional)"
            settingKey="settings-general-external_webhook_password"
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

      <Check
        label="Use Autopulse auto-configuration (requires Plex OAuth)"
        settingKey="settings-plex-use_autopulse"
      />

      {!isPlexAuthenticated && (
        <Alert variant="light" color="gray">
          Enable Plex OAuth above to use Autopulse auto-configuration.
        </Alert>
      )}

      <CollapseBox indent settingKey="settings-plex-use_autopulse">
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            Auto-configuration automatically sets up Autopulse with your
            existing Plex OAuth settings. This overrides the generic webhook
            settings above when enabled.
          </Text>

          <SettingsText
            label="Autopulse Host"
            settingKey="settings-plex-autopulse_host"
            placeholder="localhost or autopulse"
          />
          <Number
            label="Autopulse Port"
            settingKey="settings-plex-autopulse_port"
          />
          <SettingsText
            label="Username (optional)"
            settingKey="settings-plex-autopulse_username"
            placeholder="admin"
          />
          <Password
            label="Password (optional)"
            settingKey="settings-plex-autopulse_password"
          />

          <Group gap="sm">
            <Button
              onClick={handleGetPlexConfig}
              loading={isFetchingPlexConfig}
              size="sm"
              variant="light"
              disabled={!isPlexAuthenticated}
            >
              View Plex Config
            </Button>
            <Button
              onClick={handleTestConnection}
              loading={testMutation.isPending}
              size="sm"
              variant="light"
            >
              Test Connection
            </Button>
          </Group>

          {plexConfigData && (
            <Card withBorder p="sm" radius="md">
              <Text size="xs" fw={600} mb="xs">
                Available Plex Configuration:
              </Text>
              <Text size="xs" c="dimmed">
                Server: {plexConfigData.server_name || "Unknown"}
                <br />
                URL: {plexConfigData.plex_url || "Not configured"}
                <br />
                Auth: {plexConfigData.auth_method || "Unknown"}
              </Text>
            </Card>
          )}
        </Stack>
      </CollapseBox>
    </Stack>
  );
};

export default ExternalWebhookSelector;
