import { FunctionComponent } from "react";
import {
  ActionIcon,
  Alert,
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
import styles from "@/pages/Settings/Plex/WebhookSelector.module.scss";

export type AutopulseSelectorProps = {
  label: string;
  description?: string;
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
        message: "Failed to generate Autopulse configuration",
        color: "red",
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <Stack gap="xs" className={styles.webhookSelector}>
        <Text fw={500} className={styles.labelText}>
          {label}
        </Text>
        <Alert color="brand" variant="light" className={styles.alertMessage}>
          Enable Plex OAuth above to be able to generate a config for Autopulse.
        </Alert>
      </Stack>
    );
  }

  return (
    <div className={styles.webhookSelector}>
      <Stack gap="xs">
        <div>
          <Text fw={500} size="sm" mb={2}>
            {label}
          </Text>
          <Text size="xs" c="dimmed">
            {description ||
              "Generate a complete Autopulse configuration file with your Plex server details, OAuth credentials, and optimized settings. Save as bazarr-plex.toml (or any custom name) in your Autopulse container data directory."}
          </Text>
        </div>

        <Group gap="xs">
          <Button
            onClick={handleGenerateAutopulseConfig}
            loading={isFetchingConfig}
            size="sm"
            variant="light"
          >
            Generate Configuration
          </Button>
        </Group>

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
      </Stack>
    </div>
  );
};

export default AutopulseSelector;
