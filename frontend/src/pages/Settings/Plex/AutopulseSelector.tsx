import { FunctionComponent } from "react";
import { Alert, Box, Button, Code, Group, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  usePlexAuthValidationQuery,
  usePlexAutopulseConfigQuery,
  usePlexAutopulseTestMutation,
} from "@/apis/hooks/plex";
import { Check } from "@/pages/Settings/components";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";

export type AutopulseSelectorProps = {
  label: string;
  description?: string;
};

const AutopulseSelector: FunctionComponent<AutopulseSelectorProps> = (
  props,
) => {
  const { label, description } = props;

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  // Check if Autopulse is enabled
  const autopulseEnabled = useSettingValue<boolean>(
    "settings-plex-use_autopulse",
    { original: false },
  );

  const testMutation = usePlexAutopulseTestMutation();

  // Get autopulse configuration
  const {
    data: configData,
    refetch: refetchConfig,
    isFetching: isFetchingConfig,
  } = usePlexAutopulseConfigQuery({
    enabled: isAuthenticated,
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
      notifications.show({
        title: "Error",
        message: "Failed to test Autopulse connection",
        color: "red",
      });
    }
  };

  const handleGetConfig = async () => {
    try {
      const result = await refetchConfig();

      if (result.data) {
        const config = result.data;
        notifications.show({
          title: "Configuration Retrieved",
          message: `Ready to configure Autopulse with ${config.server_name}`,
          color: "green",
        });
      }
    } catch (error: unknown) {
      notifications.show({
        title: "Error",
        message: "Failed to get Autopulse configuration",
        color: "red",
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <Stack gap="xs">
        <Text fw={500}>{label}</Text>
        <Alert color="brand" variant="light">
          Enable Plex OAuth above to use Autopulse integration.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack gap="xs">
      <Check
        label="Use Autopulse for automatic Plex metadata refresh"
        settingKey="settings-plex-use_autopulse"
      />

      {description && (
        <Text size="sm" c="dimmed">
          {description}
        </Text>
      )}

      {autopulseEnabled && (
        <Stack gap="sm">
          <Group gap="xs">
            <Button
              onClick={handleTestConnection}
              loading={testMutation.isPending}
              size="sm"
              variant="light"
            >
              TEST CONNECTION
            </Button>
            <Button
              onClick={handleGetConfig}
              loading={isFetchingConfig}
              size="sm"
              variant="outline"
            >
              GET PLEX CONFIG
            </Button>
          </Group>

          {configData && (
            <Box>
              <Text size="sm" fw={500} mb="xs">
                Autopulse Configuration:
              </Text>
              <Stack gap="xs">
                <Text size="sm">
                  <Text component="span" fw={500}>
                    PLEX_URL:
                  </Text>{" "}
                  <Code>{configData.plex_url}</Code>
                </Text>
                <Text size="sm">
                  <Text component="span" fw={500}>
                    PLEX_TOKEN:
                  </Text>{" "}
                  <Code>{configData.plex_token.substring(0, 8)}...</Code>
                </Text>
                <Text size="sm">
                  <Text component="span" fw={500}>
                    Server:
                  </Text>{" "}
                  {configData.server_name} ({configData.username})
                </Text>
              </Stack>
            </Box>
          )}
        </Stack>
      )}
    </Stack>
  );
};

export default AutopulseSelector;
