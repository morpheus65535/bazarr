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
import { notifications } from "@mantine/notifications";
import { faCopy } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  usePlexAuthValidationQuery,
  usePlexAutopulseConfigQuery,
} from "@/apis/hooks/plex";
import { Message } from "@/pages/Settings/components";

export type AutopulseSelectorProps = {
  label: string;
  description?: React.ReactNode;
};

const AutopulseSelector: FunctionComponent<AutopulseSelectorProps> = (
  props,
) => {
  const { label, description } = props;

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.authMethod === "oauth",
  );

  const {
    data: configData,
    refetch: refetchConfig,
    isFetching: isFetchingConfig,
  } = usePlexAutopulseConfigQuery({
    enabled: false,
    retry: false,
  });

  const handleGenerateAutopulseConfig = async () => {
    const result = await refetchConfig();

    if (result.isSuccess && result.data) {
      notifications.show({
        id: "autopulse-config",
        title: "Success",
        message: "Autopulse configuration generated successfully",
        color: "success",
      });
    } else if (result.isError) {
      const status = (result.error as { response?: { status?: number } })
        ?.response?.status;

      const errorMessage =
        status === 401
          ? "Plex OAuth authentication required. Please configure OAuth authentication above."
          : status === 400
            ? "Unable to generate configuration. Please ensure the external webhook is configured and saved in Settings."
            : "Failed to generate Autopulse configuration. Please ensure Autopulse is running and supports the template API.";

      notifications.show({
        id: "autopulse-config",
        title: "Error",
        message: errorMessage,
        color: "danger",
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <Stack gap="xs">
        <Text fw={500} size="sm">
          {label}
        </Text>
        <Message>
          Connect to Plex above to generate an Autopulse configuration.
        </Message>
      </Stack>
    );
  }

  return (
    <Stack gap="xs">
      <Stack gap={2}>
        <Text fw={500} size="sm">
          {label}
        </Text>
        <Message>{description}</Message>
      </Stack>

      <Group gap="xs">
        <Button
          onClick={handleGenerateAutopulseConfig}
          loading={isFetchingConfig}
        >
          Generate Configuration
        </Button>

        {configData && (
          <Badge color="success" variant="light" size="sm">
            Dynamic
          </Badge>
        )}
      </Group>

      {configData && (
        <Card withBorder p="md" radius="sm">
          <Group justify="space-between" align="center" mb="xs">
            <Text size="sm" fw={600}>
              Autopulse Configuration
            </Text>
            <Tooltip label="Copy configuration">
              <ActionIcon
                aria-label="Copy configuration"
                size="sm"
                onClick={async () => {
                  const yamlContent = configData?.configYaml;

                  if (!yamlContent) {
                    notifications.show({
                      title: "Error",
                      message: "No configuration to copy",
                      color: "danger",
                    });
                    return;
                  }

                  if (!window.isSecureContext) {
                    notifications.show({
                      title: "Cannot Copy",
                      message:
                        "Clipboard access requires a secure context (HTTPS or http://localhost). Please copy manually from the code block below.",
                      color: "warning",
                    });
                    return;
                  }

                  try {
                    await navigator.clipboard.writeText(yamlContent);
                    notifications.show({
                      title: "Copied!",
                      message: "Autopulse configuration copied to clipboard",
                      color: "success",
                    });
                  } catch {
                    notifications.show({
                      title: "Copy Failed",
                      message:
                        "Failed to copy to clipboard. Please copy manually from the code block below.",
                      color: "danger",
                    });
                  }
                }}
              >
                <FontAwesomeIcon icon={faCopy} />
              </ActionIcon>
            </Tooltip>
          </Group>

          <Code block style={{ maxHeight: 300, overflow: "auto" }}>
            {configData.configYaml}
          </Code>

          <Stack gap="xs" mt="sm">
            <Text size="xs" c="dimmed">
              <Text component="span" fw={600}>
                Server:
              </Text>{" "}
              {configData.serverName}
            </Text>

            {configData.rewriteSuggestion && (
              <Alert
                color={configData.rewriteDetected ? "warning" : "brand"}
                variant="light"
              >
                <Text size="xs">
                  <Text component="span" fw={600}>
                    Configuration Notes:
                  </Text>{" "}
                  {configData.rewriteSuggestion}
                </Text>
              </Alert>
            )}

            {configData.templateInfo && (
              <Text size="xs" c="dimmed">
                {configData.templateInfo}
              </Text>
            )}
          </Stack>
        </Card>
      )}
    </Stack>
  );
};

export default AutopulseSelector;
