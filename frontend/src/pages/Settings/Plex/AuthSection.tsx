import { useEffect, useRef, useState } from "react";
import {
  Alert,
  Avatar,
  Button,
  Group,
  Loader,
  Stack,
  Text,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useQueryClient } from "@tanstack/react-query";
import {
  usePlexAuthValidationQuery,
  usePlexLogoutMutation,
  usePlexPinCheckQuery,
  usePlexPinMutation,
} from "@/apis/hooks/plex";
import { QueryKeys } from "@/apis/queries/keys";
import { PLEX_AUTH_CONFIG } from "@/constants/plex";
import { Message } from "@/pages/Settings/components";

const AuthSection = () => {
  const {
    data: authData,
    isLoading: authIsLoading,
    error: authError,
    refetch: refetchAuth,
  } = usePlexAuthValidationQuery();
  const { mutateAsync: createPin } = usePlexPinMutation();
  const { mutate: logout, isPending: isLoggingOut } = usePlexLogoutMutation();
  const [pin, setPin] = useState<Plex.Pin | null>(null);
  const authWindowRef = useRef<Window | null>(null);
  const queryClient = useQueryClient();

  const [authSucceeded, setAuthSucceeded] = useState(false);

  const isPolling = !!pin?.pinId && !authSucceeded;

  const { data: pinData } = usePlexPinCheckQuery(
    pin?.pinId ?? null,
    isPolling,
    pin?.pinId ? PLEX_AUTH_CONFIG.POLLING_INTERVAL_MS : false,
  );

  // Handle successful authentication - stop polling (adjusting state during
  // render avoids an effect-driven render cascade).
  if (pinData?.authenticated && pin?.pinId && !authSucceeded) {
    setAuthSucceeded(true);
  }

  // Close the auth window and refresh auth/server data once, when the pin
  // check first reports the user as authenticated.
  const wasHandledRef = useRef(false);

  useEffect(() => {
    if (authSucceeded && !wasHandledRef.current) {
      wasHandledRef.current = true;
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
  }, [authSucceeded, refetchAuth, queryClient]);

  const isAuthenticated = Boolean(
    authData?.valid && authData?.authMethod === "oauth",
  );

  const handleAuth = async () => {
    const { data: pin } = await createPin();

    setPin(pin);
    setAuthSucceeded(false);
    // Rearm the one-shot success handling for this new attempt
    wasHandledRef.current = false;

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
    logout(undefined, {
      onSuccess: () => {
        notifications.show({
          title: "Disconnected from Plex",
          message: "All settings related to Plex were removed",
          color: "success",
        });
      },
    });
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
    return (
      <Group gap="xs">
        <Loader size="xs" />
        <Text size="sm" c="dimmed">
          Loading authentication status...
        </Text>
      </Group>
    );
  }

  if (isPolling && !pinData?.authenticated) {
    return (
      <Stack gap="xs">
        <Message>Complete the authentication in the opened window.</Message>
        <Text>
          PIN Code:{" "}
          <Text component="span" fw={700}>
            {pin?.code}
          </Text>
        </Text>
        {authError && (
          <Alert color="danger" variant="light">
            {authError.message || "Authentication failed"}
          </Alert>
        )}
        <Group>
          <Button onClick={handleCancelAuth} variant="light" color="secondary">
            Cancel
          </Button>
        </Group>
      </Stack>
    );
  }

  if (!isAuthenticated) {
    return (
      <Stack gap="xs">
        <Message>
          Connect your Plex account to enable secure, automated integration with
          Bazarr. Manual configuration is available via config.yaml if OAuth is
          not suitable.
        </Message>
        {authError && (
          <Alert color="danger" variant="light">
            {authError.message || "Authentication failed"}
          </Alert>
        )}
        <Group>
          <Button onClick={handleAuth}>Connect to Plex</Button>
        </Group>
      </Stack>
    );
  }

  // Authenticated state
  const username = authData?.username;
  const email = authData?.email;

  return (
    <Group gap="xs" justify="space-between" align="center" wrap="wrap">
      <Group gap="xs" wrap="nowrap">
        <Avatar size="sm" radius="xl" color="brand">
          {(username ?? email ?? "P")[0].toUpperCase()}
        </Avatar>
        <Text size="sm">
          {username}{" "}
          <Text component="span" c="dimmed">
            ({email})
          </Text>
        </Text>
      </Group>
      <Button
        onClick={handleLogout}
        variant="light"
        color="secondary"
        loading={isLoggingOut}
        disabled={isLoggingOut}
      >
        Disconnect from Plex
      </Button>
    </Group>
  );
};

export default AuthSection;
