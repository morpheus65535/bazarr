import { FunctionComponent } from "react";
import { Alert, Button, Group, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  usePlexAuthValidationQuery,
  usePlexAutopulseTestMutation,
  usePlexAutopulseConfigQuery,
} from "@/apis/hooks/plex";

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

  const testMutation = usePlexAutopulseTestMutation();

  const {
    data: configData,
    refetch: refetchConfig,
    isFetching: isFetchingConfig,
  } = usePlexAutopulseConfigQuery({ enabled: false });

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
        <Text fw={500}>{label}</Text>
        <Alert variant="light">
          Enable Plex OAuth above to use Autopulse integration.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack gap="xs">
      <Group justify="space-between" align="flex-end">
        <div>
          <Text fw={500}>{label}</Text>
          {description && (
            <Text size="sm" c="dimmed">
              {description}
            </Text>
          )}
        </div>
        <Group gap="sm">
          <Button
            onClick={handleGetPlexConfig}
            loading={isFetchingConfig}
            size="sm"
            variant="outline"
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
        <Alert variant="light" color="blue">
          <Text size="sm" fw={500}>
            Plex Configuration from Autopulse:
          </Text>
          <Text size="xs">Server: {configData.server_name || "Unknown"}</Text>
          <Text size="xs">URL: {configData.plex_url || "Not configured"}</Text>
          <Text size="xs">
            Auth Method: {configData.auth_method || "Unknown"}
          </Text>
          <Text size="xs">Libraries: {configData.libraries?.length || 0}</Text>
        </Alert>
      )}
    </Stack>
  );
};

export default AutopulseSelector;
