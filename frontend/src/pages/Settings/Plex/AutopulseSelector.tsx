import { FunctionComponent } from "react";
import { Alert, Button, Group, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  usePlexAuthValidationQuery,
  usePlexAutopulseTestMutation,
} from "@/apis/hooks/plex";
import { Check } from "@/pages/Settings/components";

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
      <Group justify="space-between" align="flex-end">
        <div>
          <Text fw={500}>{label}</Text>
          {description && (
            <Text size="sm" c="dimmed">
              {description}
            </Text>
          )}
        </div>
        <Button
          onClick={handleTestConnection}
          loading={testMutation.isPending}
          size="sm"
          variant="light"
        >
          TEST CONNECTION
        </Button>
      </Group>
    </Stack>
  );
};

export default AutopulseSelector;
