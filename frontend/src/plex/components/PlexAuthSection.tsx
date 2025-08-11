import React from "react";
import { Alert, Button, Paper, Stack, Text, Title } from "@mantine/core";
import { getErrorMessage, type PlexError } from "@/plex/utilities/errors";
import styles from "./PlexSettings.module.scss";

interface PlexAuthSectionProps {
  isLoading: boolean;
  isPolling: boolean;
  isAuthenticated: boolean;
  pinData?: { code: string } | null;
  authError?: PlexError;
  username?: string;
  email?: string;
  onStartAuth: () => void;
  onCancelAuth: () => void;
  onLogout: () => void;
}

export const PlexAuthSection: React.FC<PlexAuthSectionProps> = ({
  isLoading,
  isPolling,
  isAuthenticated,
  pinData,
  authError,
  username,
  email,
  onStartAuth,
  onCancelAuth,
  onLogout,
}) => {
  if (isLoading && !isPolling) {
    return <Text>Loading authentication status...</Text>;
  }

  if (isPolling && pinData) {
    return (
      <Paper withBorder radius="md" p="lg" className={styles.authSection}>
        <Stack gap="md">
          <Title order={4}>Plex OAuth (recommended)</Title>
          <Stack gap="sm">
            <Text size="lg" fw={600}>
              Complete Authentication
            </Text>
            <Text>
              PIN Code:{" "}
              <Text component="span" fw={700}>
                {pinData.code}
              </Text>
            </Text>
            <Text size="sm">
              Complete the authentication in the opened window.
            </Text>
            <Button
              onClick={onCancelAuth}
              variant="light"
              color="gray"
              size="sm"
              className={styles.actionButton}
            >
              Cancel
            </Button>
          </Stack>
        </Stack>
      </Paper>
    );
  }

  if (!isAuthenticated) {
    return (
      <Paper withBorder radius="md" p="lg" className={styles.authSection}>
        <Stack gap="md">
          <Title order={4}>Plex OAuth (recommended)</Title>
          <Stack gap="sm">
            <Text size="sm">
              Connect your Plex account to enable secure, automated integration
              with Bazarr.
            </Text>
            {authError && (
              <Alert color="red" variant="light">
                {getErrorMessage(authError)}
              </Alert>
            )}
            <Button
              onClick={onStartAuth}
              variant="filled"
              color="brand"
              size="md"
              className={styles.actionButton}
            >
              Connect to Plex
            </Button>
          </Stack>
        </Stack>
      </Paper>
    );
  }

  // Authenticated state
  return (
    <Paper withBorder radius="md" p="lg" className={styles.authSection}>
      <Stack gap="md">
        <Title order={4}>Plex OAuth (recommended)</Title>
        <Alert color="brand" variant="light">
          Connected as {username} ({email})
        </Alert>
        <Button
          onClick={onLogout}
          variant="light"
          color="gray"
          size="sm"
          className={styles.actionButton}
        >
          Disconnect from Plex
        </Button>
      </Stack>
    </Paper>
  );
};
