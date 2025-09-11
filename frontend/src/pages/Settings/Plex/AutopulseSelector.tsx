import { FunctionComponent } from "react";
import { Alert, Button, Group, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  Check,
  CollapseBox,
  Number,
  Password,
  Text as SettingsText,
} from "@/pages/Settings/components";
import {
  usePlexAuthValidationQuery,
  usePlexAutopulseTestMutation,
  usePlexAutopulseConfigQuery,
} from "@/apis/hooks/plex";

export type AutopulseSelectorProps = {
  // No props needed since this is now a complete section
};

const AutopulseSelector: FunctionComponent<AutopulseSelectorProps> = () => {
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

      if (result.data.success) {
        notifications.show({
          title: "Success",
          message: result.data.message,
          color: "green",
        });
      } else {
        notifications.show({
          title: "Error",
          message: result.data.message,
          color: "red",
        });
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : error && typeof error === "object" && "response" in error
            ? (error as { response?: { data?: { error?: string } } }).response
                ?.data?.error
            : "Failed to test Autopulse connection";

      notifications.show({
        title: "Error",
        message: errorMessage || "Failed to test Autopulse connection",
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
          message: "Failed to get Plex configuration from Autopulse",
          color: "red",
        });
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to get Plex configuration";

      notifications.show({
        title: "Error",
        message: errorMessage,
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

        <Group justify="space-between" align="flex-end" mt="md">
          <Text fw={500}>Test Autopulse Connection</Text>
          <Group gap="sm">
            <Button
              onClick={handleGetPlexConfig}
              loading={isFetchingConfig}
              size="sm"
              variant="light"
            >
              GET PLEX CONFIG
            </Button>
            <Button
              onClick={handleTestConnection}
              loading={testMutation.isPending}
              size="sm"
              variant="light"
            >
              TEST CONNECTION
            </Button>
          </Group>
        </Group>

        {configData && (
          <Alert variant="light" color="brand">
            Plex Configuration for Autopulse:
          </Alert>
        )}

        {configData && (
          <Alert variant="filled" color="gray" p="md">
            <Text
              size="xs"
              style={{
                fontFamily: "monospace",
                whiteSpace: "pre-wrap",
                color: "var(--mantine-color-dark-0)",
                lineHeight: 1.4,
              }}
            >
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
            </Text>
          </Alert>
        )}

        <Alert variant="light" color="brand">
          Minimal Docker Compose Setup:
        </Alert>

        <Alert variant="filled" color="gray" p="md">
          <Text
            size="xs"
            style={{
              fontFamily: "monospace",
              whiteSpace: "pre-wrap",
              color: "var(--mantine-color-dark-0)",
              lineHeight: 1.4,
            }}
          >
            {`services:
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
      - AUTOPULSE__AUTH__PASSWORD=password`}
          </Text>
        </Alert>
      </CollapseBox>
    </Stack>
  );
};

export default AutopulseSelector;
