import { FunctionComponent, useState } from "react";
import { Alert, Button, Group, Select, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  usePlexAuthValidationQuery,
  usePlexWebhookCreateMutation,
  usePlexWebhookDeleteMutation,
  usePlexWebhookListQuery,
} from "@/apis/hooks/plex";
import { useInstanceName } from "@/apis/hooks/site";
import { Message } from "@/pages/Settings/components";

export type WebhookSelectorProps = {
  label: string;
  description?: string;
};

const WebhookSelector: FunctionComponent<WebhookSelectorProps> = (props) => {
  const { label, description } = props;
  const [selectedWebhookUrl, setSelectedWebhookUrl] = useState<string>("");

  // Get this instance's name for webhook matching
  const instanceName = useInstanceName();

  // Check if user is authenticated with OAuth
  const { data: authData } = usePlexAuthValidationQuery();
  const isAuthenticated = Boolean(
    authData?.valid && authData?.authMethod === "oauth",
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

  // Find the Bazarr webhook for THIS instance (check instance= parameter)
  const bazarrWebhook = webhooks?.webhooks?.find((w) => {
    if (!w.url.includes("/api/webhooks/plex")) return false;
    // Check if the webhook belongs to this instance
    const encodedInstanceName = encodeURIComponent(instanceName || "Bazarr");
    return w.url.includes(`instance=${encodedInstanceName}`);
  });

  // Check Plex Pass subscription status for webhooks feature
  const plexPassSubscription = webhooks?.plexPassSubscription;
  const hasWebhooksFeature = plexPassSubscription?.hasWebhooksFeature ?? true;

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
        color: "success",
      });
      await refetch();
    } catch {
      notifications.show({
        title: "Error",
        message: "Failed to create webhook",
        color: "danger",
      });
    }
  };

  const handleDeleteWebhook = async (webhookUrl: string) => {
    try {
      await deleteMutation.mutateAsync(webhookUrl);
      notifications.show({
        title: "Success",
        message: "Webhook deleted successfully",
        color: "success",
      });
      // Clear selection if we deleted the currently selected webhook
      if (webhookUrl === currentValue) {
        setSelectedWebhookUrl("");
      }
      await refetch();
    } catch {
      notifications.show({
        title: "Error",
        message: "Failed to delete webhook",
        color: "danger",
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <Stack gap="xs">
        <Text fw={500}>{label}</Text>
        <Message>
          Connect to Plex above to automatically discover your webhooks.
        </Message>
      </Stack>
    );
  }

  if (isLoading) {
    return (
      <Select
        label={label}
        placeholder="Loading webhooks..."
        data={[]}
        disabled
      />
    );
  }

  if (error) {
    return (
      <Stack gap="xs">
        <Text fw={500}>{label}</Text>
        <Alert color="danger" variant="light">
          Failed to load webhooks:{" "}
          {(error as Error)?.message || "Unknown error"}
        </Alert>
      </Stack>
    );
  }

  if (selectData.length === 0) {
    return (
      <Stack gap="xs">
        <Group justify="space-between" align="flex-end">
          <Stack gap={2}>
            <Text fw={500}>{label}</Text>
            {description && (
              <Text size="sm" c="dimmed">
                {description}
              </Text>
            )}
          </Stack>
          <Button
            onClick={handleCreateWebhook}
            loading={createMutation.isPending}
            size="sm"
            disabled={!hasWebhooksFeature}
          >
            Add
          </Button>
        </Group>
        {!hasWebhooksFeature && (
          <Alert color="warning" variant="light">
            Webhooks require a Plex Pass subscription.{" "}
            <a
              href="https://www.plex.tv/plans/"
              target="_blank"
              rel="noopener noreferrer"
            >
              Learn more
            </a>
          </Alert>
        )}
        {hasWebhooksFeature && (
          <Alert color="secondary" variant="light">
            No webhooks found on your Plex server.
          </Alert>
        )}
      </Stack>
    );
  }

  return (
    <Stack gap="xs">
      {!hasWebhooksFeature && (
        <Alert color="warning" variant="light">
          Webhooks require a Plex Pass subscription.{" "}
          <a
            href="https://www.plex.tv/plans/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Learn more
          </a>
        </Alert>
      )}
      <Select
        data-testid="webhook-select"
        label={label}
        description={
          description ||
          "Create or remove webhooks in Plex to trigger subtitle searches. In this list you can find your current webhooks."
        }
        placeholder="Select webhook..."
        data={selectData}
        value={currentValue}
        onChange={(value) => setSelectedWebhookUrl(value || "")}
        allowDeselect={false}
      />

      <Group gap="xs">
        {!bazarrWebhook && (
          <Button
            onClick={handleCreateWebhook}
            loading={createMutation.isPending}
            size="sm"
            disabled={!hasWebhooksFeature}
          >
            Add
          </Button>
        )}

        {currentValue && (
          <Button
            onClick={() => handleDeleteWebhook(currentValue)}
            loading={deleteMutation.isPending}
            size="sm"
            color="danger"
          >
            Remove
          </Button>
        )}
      </Group>
    </Stack>
  );
};

export default WebhookSelector;
