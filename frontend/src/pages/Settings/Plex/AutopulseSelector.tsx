import { FunctionComponent, useState } from "react";
import {
  ActionIcon,
  Alert,
  Button,
  Card,
  Code,
  Collapse,
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
  usePlexAutopulseScanMutation,
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
  const [dockerExampleOpen, setDockerExampleOpen] = useState(false);
  const clipboard = useClipboard();

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  const testMutation = usePlexAutopulseTestMutation();
  const scanMutation = usePlexAutopulseScanMutation();

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

  const handleGetPlexConfig = async () => {
    try {
      const result = await refetchConfig();
      if (result.data) {
        notifications.show({
          title: "Success",
          message: `Found Plex config: ${result.data.server_name || "Server"}`,
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

  // Docker Compose YAML content
  const dockerComposeYaml = `services:
  autopulse:
    image: ghcr.io/dan-online/autopulse:latest
    container_name: autopulse
    restart: unless-stopped
    ports:
      - "2875:2875"
    volumes:
      - ./data:/app/data
    environment:
      - AUTOPULSE__APP__DATABASE_URL=sqlite://data/autopulse.db
      - AUTOPULSE__AUTH__USERNAME=admin
      - AUTOPULSE__AUTH__PASSWORD=password`;

  const handleCopyDockerCompose = () => {
    clipboard.copy(dockerComposeYaml);
    notifications.show({
      title: "Copied!",
      message: "Docker Compose configuration copied to clipboard",
      color: "green",
    });
  };

  const handleTriggerScan = async (scanType: "recent" | "all") => {
    try {
      const result = await scanMutation.mutateAsync(scanType);
      notifications.show({
        title: result.data.success ? "Success" : "Error",
        message: result.data.message,
        color: result.data.success ? "green" : "red",
      });
    } catch (error) {
      notifications.show({
        title: "Error",
        message: "Failed to trigger Autopulse scan",
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
          How to Set Up Autopulse:
        </Text>
        <Text size="sm" c="dimmed" mb="md">
          For Autopulse to work with Bazarr, you need to:
        </Text>
        <List size="sm" spacing="xs" withPadding>
          <List.Item>
            Deploy Autopulse using Docker (see example below)
          </List.Item>
          <List.Item>
            Set the Autopulse host/port in the settings below
          </List.Item>
          <List.Item>
            Autopulse will automatically use your existing Plex OAuth
            configuration from Bazarr
          </List.Item>
          <List.Item>Test the connection to ensure it's working</List.Item>
        </List>
        <Text size="sm" c="dimmed" mt="sm">
          No manual Plex configuration needed in Autopulse - it's handled
          automatically using Bazarr's existing settings.
        </Text>
      </Card>

      <Card withBorder p="md" radius="md">
        <Group justify="space-between" align="center" mb="xs">
          <Text size="sm" fw={600}>
            Docker Compose Example
          </Text>
          <Group gap="xs">
            <Tooltip label="Copy to clipboard">
              <ActionIcon
                variant="subtle"
                size="sm"
                onClick={handleCopyDockerCompose}
                disabled={!dockerExampleOpen}
              >
                <FontAwesomeIcon
                  icon={clipboard.copied ? faCheck : faCopy}
                  color={clipboard.copied ? "green" : undefined}
                />
              </ActionIcon>
            </Tooltip>
            <Button
              variant="subtle"
              size="xs"
              onClick={() => setDockerExampleOpen(!dockerExampleOpen)}
            >
              {dockerExampleOpen ? "Hide" : "Show"}
            </Button>
          </Group>
        </Group>
        <Collapse in={dockerExampleOpen}>
          <Code block mt="xs" style={{ position: "relative" }}>
            {dockerComposeYaml}
          </Code>
        </Collapse>
      </Card>

      <CollapseBox indent settingKey="settings-plex-use_autopulse">
        <SettingsText
          label="Autopulse Host"
          settingKey="settings-plex-autopulse_host"
          placeholder="localhost or docker container name"
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
          <Text fw={500}>Test Autopulse Integration</Text>
          <Group gap="sm">
            <Button
              onClick={handleGetPlexConfig}
              loading={isFetchingConfig}
              size="sm"
              variant="light"
            >
              VIEW PLEX CONFIG
            </Button>
            <Button
              onClick={handleTestConnection}
              loading={testMutation.isPending}
              size="sm"
              variant="light"
            >
              TEST AUTOPULSE CONNECTION
            </Button>
          </Group>
          <Text size="xs" c="dimmed">
            "View Plex Config" shows what Autopulse will receive from Bazarr's
            Plex OAuth. "Test Autopulse Connection" verifies communication with
            your Autopulse server.
          </Text>
        </Stack>

        <Stack gap="xs" mt="md">
          <Text fw={500}>Trigger Autopulse Scan</Text>
          <Text size="xs" c="dimmed" mb="sm">
            Manually trigger Autopulse to refresh items in your Plex libraries.
          </Text>
          <Group gap="sm">
            <Button
              onClick={() => handleTriggerScan("recent")}
              loading={scanMutation.isPending}
              size="sm"
              variant="light"
            >
              SCAN RECENTLY ADDED
            </Button>
            <Button
              onClick={() => handleTriggerScan("all")}
              loading={scanMutation.isPending}
              size="sm"
              variant="filled"
            >
              SCAN ALL ITEMS
            </Button>
          </Group>
          <Text size="xs" c="dimmed">
            <strong>Recently Added:</strong> Scans items recently added to Plex.
            <strong> All Items:</strong> Scans all items in your libraries (use
            with caution on large libraries).
          </Text>
        </Stack>

        {configData && (
          <Card withBorder p="md" radius="md" mt="md">
            <Text size="sm" fw={600} mb="xs">
              Plex Configuration (Auto-detected from Bazarr):
            </Text>
            <Text size="xs" c="dimmed" mb="sm">
              This is what Autopulse will automatically receive from Bazarr's
              Plex OAuth:
            </Text>
            <Code block>
              {`Server: ${configData.server_name || "Unknown"}
URL: ${configData.plex_url || "Not configured"}
Auth Method: ${configData.auth_method || "Unknown"}
Libraries: ${configData.libraries?.length || 0}
Library Paths: ${
                configData.libraries && configData.libraries.length > 0
                  ? configData.libraries
                      .map((lib) => lib.locations.join(", "))
                      .join("; ")
                  : "None"
              }`}
            </Code>
          </Card>
        )}
      </CollapseBox>
    </Stack>
  );
};

export default AutopulseSelector;
