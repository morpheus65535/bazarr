import { useRef, useState } from "react";
import { Alert, Button, Paper, Stack, Text, Title } from "@mantine/core";
import {
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
} from "@/apis/hooks/plex";
import { PLEX_AUTH_CONFIG } from "@/constants/plex";
import styles from "@/pages/Settings/Plex/PlexSettings.module.scss";

interface AuthSectionProps {
  onCancelAuth: () => void;
  onLogout: () => void;
}

const AuthSection = ({ onCancelAuth, onLogout }: AuthSectionProps) => {
  const authQuery = usePlexAuthValidationQuery();
  const pinMutation = usePlexPinMutation();
  const logoutMutation = usePlexLogoutMutation();

  const [pin, setPin] = useState<Plex.Pin | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const authWindowRef = useRef<Window | null>(null);
  const pollIntervalRef = useRef<number | null>(null);

  // TODO: Add Maximum Attempts for Polling
  // TODO: Handle Polling Errors
  // TODO: Close Window

  const pinCheckQuery = usePlexPinCheckQuery(pin?.pinId ?? null, false);

  const isAuthenticated =
    authQuery.data?.valid && authQuery.data?.auth_method === "oauth";

  // Simple polling with native setTimeout
  const startPolling = () => {
    if (pollIntervalRef.current) return; // Already polling

    const poll = () => {
      if (pollCount >= PLEX_AUTH_CONFIG.MAX_POLLING_ATTEMPTS) {
        stopPolling();
        return;
      }

      pinCheckQuery.refetch();
      setPollCount((prev) => prev + 1);
      pollIntervalRef.current = window.setTimeout(
        poll,
        PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS,
      );
    };

    poll();
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearTimeout(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  // Simple handlers
  const handleAuth = async () => {
    const { data: pinData } = await pinMutation.mutateAsync();
    setPin(pinData);
    setPollCount(0);

    const { width, height, features } = PLEX_AUTH_CONFIG.AUTH_WINDOW_CONFIG;
    const left = Math.round(window.screen.width / 2 - width / 2);
    const top = Math.round(window.screen.height / 2 - height / 2);

    authWindowRef.current = window.open(
      pinData.authUrl,
      "PlexAuth",
      `width=${width},height=${height},left=${left},top=${top},${features}`,
    );

    // Start polling after opening auth window
    startPolling();
  };

  const handleCancel = () => {
    stopPolling();
    setPin(null);
    setPollCount(0);
    if (authWindowRef.current) {
      authWindowRef.current.close();
    }
    onCancelAuth();
  };

  const handleLogout = () => {
    stopPolling();
    logoutMutation.mutate();
    onLogout();
  };

  const isPolling = !!pin?.pinId && !!pollIntervalRef.current;

  if (authQuery.isLoading && !isPolling) {
    return <Text>Loading authentication status...</Text>;
  }

  if (isPolling && pinCheckQuery.data) {
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
                {pin?.code}
              </Text>
            </Text>
            <Text size="sm">
              Complete the authentication in the opened window.
            </Text>
            <Button
              onClick={handleCancel}
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
            {authQuery.error && (
              <Alert color="red" variant="light">
                {authQuery.error.message || "Authentication failed"}
              </Alert>
            )}
            <Button
              onClick={handleAuth}
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
          Connected as {authQuery.data?.username} ({authQuery.data?.email})
        </Alert>
        <Button
          onClick={handleLogout}
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

export default AuthSection;
