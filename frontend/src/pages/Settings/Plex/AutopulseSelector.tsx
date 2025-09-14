import { FunctionComponent } from "react";
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Card,
  Code,
  Group,
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
} from "@/apis/hooks/plex";
import styles from "@/pages/Settings/Plex/AutopulseSelector.module.scss";

export type AutopulseSelectorProps = {
  label: string;
  description?: React.ReactNode;
};

const AutopulseSelector: FunctionComponent<AutopulseSelectorProps> = (
  props,
) => {
  const { label, description } = props;
  const clipboard = useClipboard();

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  const {
    data: configData,
    refetch: refetchConfig,
    isFetching: isFetchingConfig,
  } = usePlexAutopulseConfigQuery({
    enabled: false,
  });

  const handleGenerateAutopulseConfig = async () => {
    try {
      await refetchConfig();
      notifications.show({
        title: "Success",
        message: "Autopulse configuration generated successfully",
        color: "green",
      });
    } catch (error) {
      notifications.show({
        title: "Error",
        message:
          "Failed to generate Autopulse configuration. Please ensure Autopulse is running and supports the template API.",
        color: "red",
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <Stack gap="xs" className={styles.autopulseSelector}>
        <Text fw={500} size="sm" className={styles.labelText}>
          {label}
        </Text>
        <Alert color="brand" variant="light" className={styles.alertMessage}>
          Enable Plex OAuth above to generate an Autopulse configuration.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack gap="xs" className={styles.autopulseSelector}>
      <div>
        <Text fw={500} size="sm" mb={2} className={styles.labelText}>
          {label}
        </Text>
        <Text size="xs" c="dimmed">
          {description}
        </Text>
      </div>

      <Group gap="xs">
        <Button
          onClick={handleGenerateAutopulseConfig}
          loading={isFetchingConfig}
          size="sm"
          variant="light"
          className={styles.generateButton}
        >
          Generate Configuration
        </Button>

        {configData && (
          <Badge color="green" variant="light" size="sm">
            Dynamic
          </Badge>
        )}
      </Group>

      {configData && (
        <Card
          withBorder
          p="md"
          radius="md"
          mt="md"
          className={styles.configCard}
        >
          <Group justify="space-between" align="center" mb="xs">
            <Group gap="xs">
              <Text size="sm" fw={600}>
                Autopulse Configuration
              </Text>
            </Group>
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

          <Code block className={styles.configCodeBlock}>
            {configData.config_yaml}
          </Code>

          <Stack gap="xs" mt="sm">
            <Text size="xs" c="dimmed">
              <Text component="span" fw={600}>
                Server:
              </Text>{" "}
              {configData.server_name}
            </Text>

            {configData.rewrite_suggestion && (
              <Alert
                color={configData.rewrite_detected ? "yellow" : "brand"}
                variant="light"
                className={styles.alertMessage}
              >
                <Text size="xs">
                  <Text component="span" fw={600}>
                    Configuration Notes:
                  </Text>{" "}
                  {configData.rewrite_suggestion}
                </Text>
              </Alert>
            )}

            {configData.template_info && (
              <Text size="xs" c="dimmed">
                {configData.template_info}
              </Text>
            )}
          </Stack>
        </Card>
      )}
    </Stack>
  );
};

export default AutopulseSelector;
