import { FunctionComponent, useState } from "react";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Card,
  Divider,
  LoadingOverlay,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useDocumentTitle } from "@mantine/hooks";
import { useSystem } from "@/apis/hooks";
import { Environment } from "@/utilities";
import styles from "./Authentication.module.scss";

const Authentication: FunctionComponent = () => {
  useDocumentTitle("Login - Bazarr");
  const { login, isLoggingIn } = useSystem();
  const [error, setError] = useState<string | null>(null);
  const oidc = Environment.authType === "oidc";
  const params = new URLSearchParams(window.location.search);
  const oidcError = params.get("oidcError");
  const oidcLoginUrl = `${Environment.baseUrl}/auth/oidc/login?${new URLSearchParams(
    {
      returnTo: params.get("returnTo") ?? "/",
    },
  )}`;

  const form = useForm({
    initialValues: {
      username: "",
      password: "",
    },
    validate: {
      username: (value) =>
        value.trim().length === 0 ? "Username is required" : null,
      password: (value) =>
        value.trim().length === 0 ? "Password is required" : null,
    },
  });

  return (
    <Box className={styles.root}>
      <Box maw={400} w="100%">
        <Card
          className={styles.card}
          shadow="xl"
          padding="lg"
          radius="md"
          pos="relative"
        >
          <LoadingOverlay
            visible={isLoggingIn}
            overlayProps={{ radius: "md", blur: 2 }}
          />
          <Stack gap="md">
            <Stack align="center" gap="xs">
              <Avatar
                alt="Bazarr logo"
                size={64}
                src={`${Environment.baseUrl}/images/logo128.png`}
              />
              <Title order={3}>Bazarr</Title>
              <Text c="dimmed" size="sm">
                Sign in to continue
              </Text>
            </Stack>
            <Divider />
            {oidc ? (
              <Stack gap="md">
                {oidcError && (
                  <Alert aria-live="assertive" color="red" variant="light">
                    {oidcError === "denied"
                      ? "Your account does not have access to Bazarr. Contact the administrator."
                      : "Unable to sign in. Try again or contact the administrator."}
                  </Alert>
                )}
                <Button component="a" href={oidcLoginUrl} fullWidth size="md">
                  Sign in with OpenID Connect
                </Button>
              </Stack>
            ) : (
              <form
                onSubmit={form.onSubmit((values) => {
                  setError(null);
                  login(values, {
                    onError: (err) => {
                      setError(
                        err instanceof Error ? err.message : "Login failed",
                      );
                    },
                  });
                })}
              >
                <Stack gap="md">
                  {error && (
                    <Alert aria-live="assertive" color="red" variant="light">
                      {error}
                    </Alert>
                  )}
                  <TextInput
                    autoComplete="username"
                    autoFocus
                    disabled={isLoggingIn}
                    label="Username"
                    name="username"
                    placeholder="Enter username"
                    required
                    {...form.getInputProps("username")}
                  />
                  <PasswordInput
                    autoComplete="current-password"
                    disabled={isLoggingIn}
                    label="Password"
                    name="password"
                    placeholder="Enter password"
                    required
                    {...form.getInputProps("password")}
                  />
                  <Button
                    fullWidth
                    loading={isLoggingIn}
                    size="md"
                    tt="uppercase"
                    type="submit"
                  >
                    Login
                  </Button>
                </Stack>
              </form>
            )}
          </Stack>
        </Card>
      </Box>
    </Box>
  );
};

export default Authentication;
