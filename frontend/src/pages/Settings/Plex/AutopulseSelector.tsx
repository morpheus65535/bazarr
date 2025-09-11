import { FunctionComponent } from "react";
import { Link } from "react-router";
import {
  ActionIcon,
  Alert,
  Button,
  Card,
  Code,
  Group,
  List,
  Stack,
  Text,
  Tooltip,
} from "@mantine/core";
import { useClipboard } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { faCheck, faCopy } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
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

const AutopulseSelector: FunctionComponent = () => {
  const clipboard = useClipboard();

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  const testMutation = usePlexAutopulseTestMutation();

  const {
    data: configData,
    refetch: refetchConfig,
    isFetching: isFetchingConfig,
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
        message: "Failed to test Autopulse connection",
        color: "red",
      });
    }
  };

  const handleGenerateAutopulseConfig = async () => {
    try {
      const result = await refetchConfig();
      if (result.data) {
        notifications.show({
          title: "Success",
          message: `Generated Autopulse config for: ${result.data.server_name}`,
          color: "green",
        });
      } else {
        notifications.show({
          title: "Error",
          message: "Failed to generate Autopulse configuration",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: "Failed to generate Autopulse configuration",
        color: "red",
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <Stack gap="xs">
        <Alert variant="light" color="gray">
          Enable Plex OAuth above to use Autopulse integration.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack gap="md">
      <Check
        label="Use Autopulse for automatic Plex metadata refresh"
        settingKey="settings-plex-use_autopulse"
      />

      <Card withBorder p="md" radius="md">
        <Text size="sm" fw={600} mb="xs">
          How to Set Up Autopulse Integration:
        </Text>
        <Text size="sm" c="dimmed" mb="md">
          Complete setup flow for Autopulse with Plex OAuth:
        </Text>
        <List size="sm" spacing="xs" withPadding>
          <List.Item>
            Install and run Autopulse server (see Autopulse documentation)
          </List.Item>
          <List.Item>
            Enable external webhook in{" "}
            <Text
              component={Link}
              to="/settings/general"
              fw={500}
              c="blue"
              td="none"
            >
              General Settings → External Integrations
            </Text>
          </List.Item>
          <List.Item>
            Enable Autopulse integration below and set host/port
          </List.Item>
          <List.Item>
            Generate the complete Autopulse configuration (includes Plex OAuth)
          </List.Item>
          <List.Item>
            Save the configuration as <Code>config.toml</Code> in your Autopulse
            data directory
          </List.Item>
          <List.Item>Test the connection to ensure it's working</List.Item>
        </List>
        <Text size="sm" c="dimmed" mt="sm">
          Bazarr will automatically generate a complete Autopulse configuration
          with your Plex OAuth settings and intelligent path rewriting.
        </Text>
      </Card>

      <CollapseBox indent settingKey="settings-plex-use_autopulse">
        <SettingsText
          label="Autopulse Host"
          settingKey="settings-plex-autopulse_host"
          placeholder="localhost or autopulse.example.com"
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

        <Stack gap="xs" mt="md">
          <Text fw={500}>Generate Configuration & Test Connection</Text>
          <Group gap="sm">
            <Button
              onClick={handleGenerateAutopulseConfig}
              loading={isFetchingConfig}
              size="sm"
              variant="light"
            >
              Generate Autopulse Config
            </Button>
            <Button
              onClick={handleTestConnection}
              loading={testMutation.isPending}
              size="sm"
              variant="light"
            >
              Test Autopulse Connection
            </Button>
          </Group>
          <Text size="xs" c="dimmed">
            Generate creates a complete configuration with Plex OAuth settings.
            Test verifies communication with your Autopulse server.
          </Text>
        </Stack>

        {configData && (
          <Card withBorder p="md" radius="md" mt="md">
            <Group justify="space-between" align="center" mb="xs">
              <Text size="sm" fw={600}>
                Complete Autopulse Configuration
              </Text>
              <Tooltip label="Copy configuration">
                <ActionIcon
                  variant="subtle"
                  size="sm"
                  onClick={() => {
                    clipboard.copy(configData.config_yaml);
                    notifications.show({
                      title: "Copied!",
                      message: "Autopulse configuration copied to clipboard",
                      color: "green",
                    });
                  }}
                >
                  <FontAwesomeIcon
                    icon={clipboard.copied ? faCheck : faCopy}
                    color={clipboard.copied ? "green" : undefined}
                  />
                </ActionIcon>
              </Tooltip>
            </Group>
            <Text size="xs" c="dimmed" mb="sm">
              Save this as <Code>config.toml</Code> in your Autopulse container
              data directory:
            </Text>
            {configData.rewrite_detected && (
              <Alert variant="light" color="blue" mb="sm">
                <Text size="xs">
                  <strong>Path rewriting detected:</strong>{" "}
                  {configData.rewrite_suggestion}
                </Text>
              </Alert>
            )}
            <Code block style={{ maxHeight: "300px", overflow: "auto" }}>
              {configData.config_yaml}
            </Code>
            <Text size="xs" c="dimmed" mt="sm">
              <strong>Server:</strong> {configData.server_name} |
              <strong> Rewrite needed:</strong>{" "}
              {configData.rewrite_detected ? "Yes" : "No"}
            </Text>
          </Card>
        )}
      </CollapseBox>
    </Stack>
  );
};

export default AutopulseSelector;
