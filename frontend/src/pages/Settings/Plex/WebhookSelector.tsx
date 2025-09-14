import { FunctionComponent, useState } from "react";
import { Alert, Button, Group, Select, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  usePlexAuthValidationQuery,
  usePlexWebhookCreateMutation,
  usePlexWebhookDeleteMutation,
  usePlexWebhookListQuery,
} from "@/apis/hooks/plex";
import styles from "@/pages/Settings/Plex/WebhookSelector.module.scss";

export type WebhookSelectorProps = {
  label: string;
  description?: string;
};

const WebhookSelector: FunctionComponent<WebhookSelectorProps> = (props) => {
  const { label, description } = props;
  const [selectedWebhookUrl, setSelectedWebhookUrl] = useState<string>("");

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.auth_method === "oauth",
  );

  // Fetch webhooks if authenticated
  const {
    data: webhooks,
    isLoading,
    error,
    refetch,
  } = usePlexWebhookListQuery({
    enabled: isAuthenticated,
  });

  const createMutation = usePlexWebhookCreateMutation();
  const deleteMutation = usePlexWebhookDeleteMutation();

  // Find the Bazarr webhook
  const bazarrWebhook = webhooks?.webhooks?.find((w) =>
    w.url.includes("/api/webhooks/plex"),
  );

  // Create select data with Bazarr webhook first if it exists
  const selectData =
    webhooks?.webhooks
      ?.map((webhook) => ({
        value: webhook.url,
        label: webhook.url,
        isBazarr: webhook.url.includes("/api/webhooks/plex"),
      }))
      .sort((a, b) => Number(b.isBazarr) - Number(a.isBazarr))
      .map(({ value, label }) => ({ value: value, label: label })) || [];

  // Determine the current value: prioritize user selection, fallback to bazarr webhook or first webhook
  const currentValue =
    selectedWebhookUrl ||
    bazarrWebhook?.url ||
    (selectData.length > 0 ? selectData[0].value : "");

  const handleCreateWebhook = async () => {
    try {
      await createMutation.mutateAsync();
      notifications.show({
        title: "Success",
        message: "Plex webhook created successfully",
        color: "green",
      });
      await refetch();
    } catch (error) {
      notifications.show({
        title: "Error",
        message: "Failed to create webhook",
        color: "red",
      });
    }
  };

  const handleDeleteWebhook = async (webhookUrl: string) => {
    try {
      await deleteMutation.mutateAsync(webhookUrl);
      notifications.show({
        title: "Success",
        message: "Webhook deleted successfully",
        color: "green",
      });
      // Clear selection if we deleted the currently selected webhook
      if (webhookUrl === currentValue) {
        setSelectedWebhookUrl("");
      }
      await refetch();
    } catch (error) {
      notifications.show({
        title: "Error",
        message: "Failed to delete webhook",
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
          Enable Plex OAuth above to automatically discover your webhooks.
        </Alert>
      </Stack>
    );
  }

  if (isLoading) {
    return (
      <Stack gap="xs" className={styles.webhookSelector}>
        <Select
          label={label}
          placeholder="Loading webhooks..."
          data={[]}
          disabled
          className={styles.loadingField}
        />
      </Stack>
    );
  }

  if (error) {
    return (
      <Stack gap="xs" className={styles.webhookSelector}>
        <Alert color="red" variant="light" className={styles.alertMessage}>
          Failed to load webhooks:{" "}
          {(error as Error)?.message || "Unknown error"}
        </Alert>
      </Stack>
    );
  }

  if (selectData.length === 0) {
    return (
      <div className={styles.webhookSelector}>
        <Stack gap="xs">
          <Group justify="space-between" align="flex-end">
            <div>
              <Text fw={500} className={styles.labelText}>
                {label}
              </Text>
              {description && (
                <Text size="sm" c="dimmed">
                  {description}
                </Text>
              )}
            </div>
            <Button
              onClick={handleCreateWebhook}
              loading={createMutation.isPending}
              size="sm"
            >
              Add
            </Button>
          </Group>
          <Alert color="brand" variant="light" className={styles.alertMessage}>
            No webhooks found on your Plex server.
          </Alert>
        </Stack>
      </div>
    );
  }

  return (
    <div className={styles.webhookSelector}>
      <Stack gap="xs">
        <Select
          label={label}
          placeholder="Select webhook..."
          data={selectData}
          description={
            description ||
            "Create or remove webhooks in Plex to trigger subtitle searches. In this list you can find your current webhooks."
          }
          value={currentValue}
          onChange={(value) => setSelectedWebhookUrl(value || "")}
          allowDeselect={false}
          className={styles.selectField}
        />

        <Group gap="xs">
          {!bazarrWebhook && (
            <Button
              onClick={handleCreateWebhook}
              loading={createMutation.isPending}
              size="sm"
            >
              Add
            </Button>
          )}

          {currentValue && (
            <Button
              onClick={() => handleDeleteWebhook(currentValue)}
              loading={deleteMutation.isPending}
              size="sm"
              variant="light"
              color="brand"
            >
              Remove
            </Button>
          )}
        </Group>
      </Stack>
    </div>
  );
};

export default WebhookSelector;
