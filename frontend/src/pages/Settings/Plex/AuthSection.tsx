import { useRef, useState } from "react";
import { Alert, Button, Paper, Stack, Text, Title } from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";
import {
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
} from "@/apis/hooks/plex";
import { QueryKeys } from "@/apis/queries/keys";
import { PLEX_AUTH_CONFIG } from "@/constants/plex";
import styles from "@/pages/Settings/Plex/AuthSection.module.scss";

const AuthSection = () => {
  const {
    data: authData,
    isLoading: authIsLoading,
    error: authError,
    refetch: refetchAuth,
  } = usePlexAuthValidationQuery();
  const { mutateAsync: createPin } = usePlexPinMutation();
  const { mutate: logout } = usePlexLogoutMutation();
  const [pin, setPin] = useState<Plex.Pin | null>(null);
  const authWindowRef = useRef<Window | null>(null);
  const queryClient = useQueryClient();

  const isPolling = !!pin?.pinId;

  const { data: pinData } = usePlexPinCheckQuery(
    pin?.pinId ?? null,
    isPolling,
    pin?.pinId ? PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS : false,
  );

  // Handle successful authentication - stop polling and close window
  if (pinData?.authenticated && isPolling) {
    setPin(null);
    if (authWindowRef.current) {
      authWindowRef.current.close();
      authWindowRef.current = null;
    }
    // Trigger refetch and invalidate server queries
    void refetchAuth();
    void queryClient.invalidateQueries({
      queryKey: [QueryKeys.Plex, "servers"],
    });
    void queryClient.invalidateQueries({
      queryKey: [QueryKeys.Plex, "selectedServer"],
    });
  }

  const isAuthenticated = Boolean(
    // eslint-disable-next-line camelcase
    authData?.valid && authData?.auth_method === "oauth",
  );

  const handleAuth = async () => {
    const { data: pin } = await createPin();

    setPin(pin);

    const { width, height, features } = PLEX_AUTH_CONFIG.AUTH_WINDOW_CONFIG;
    const left = Math.round(window.screen.width / 2 - width / 2);
    const top = Math.round(window.screen.height / 2 - height / 2);

    authWindowRef.current = window.open(
      pin.authUrl,
      "PlexAuth",
      `width=${width},height=${height},left=${left},top=${top},${features}`,
    );
  };

  const handleLogout = () => {
    logout();
    // No additional cleanup needed - logout mutation handles invalidation
  };

  const handleCancelAuth = () => {
    setPin(null);
    if (authWindowRef.current) {
      authWindowRef.current.close();
      authWindowRef.current = null;
    }
    // Refetch auth status when auth is cancelled
    void refetchAuth();
  };

  if (authIsLoading && !isPolling) {
    return <Text>Loading authentication status...</Text>;
  }

  if (isPolling && !pinData?.authenticated) {
    return (
      <Paper withBorder radius="md" p="lg" className={styles.authSection}>
        <Stack gap="md">
          <Title order={4}>Plex OAuth</Title>
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
              onClick={handleCancelAuth}
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
          <Title order={4}>Plex OAuth</Title>
          <Stack gap="sm">
            <Text size="sm">
              Connect your Plex account to enable secure, automated integration
              with Bazarr.
            </Text>
            <Text size="xs" c="dimmed">
              Advanced users: Manual configuration is available via config.yaml
              if OAuth is not suitable.
            </Text>
            {authError && (
              <Alert color="red" variant="light">
                {authError.message || "Authentication failed"}
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
        <Title order={4}>Plex OAuth</Title>
        <Alert color="brand" variant="light" className={styles.authAlert}>
          Connected as {authData?.username} ({authData?.email})
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
