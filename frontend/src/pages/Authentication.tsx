import { useSystem } from "@/apis/hooks";
import { useReduxStore } from "@/modules/redux/hooks/base";
import {
  Avatar,
  Button,
  Card,
  Container,
  Divider,
  PasswordInput,
  Stack,
  TextInput,
} from "@mantine/core";
import { useForm } from "@mantine/hooks";
import { FunctionComponent } from "react";
import { Navigate } from "react-router-dom";

const Authentication: FunctionComponent = () => {
  const { login } = useSystem();

  const form = useForm({
    initialValues: {
      username: "",
      password: "",
    },
  });

  const authenticated = useReduxStore(
    (s) => s.site.status !== "unauthenticated"
  );

  if (authenticated) {
    return <Navigate to="/"></Navigate>;
  }

  return (
    <Container my="xl" size={400}>
      <Card shadow="xl">
        <Stack>
          <Avatar mx="auto" size={64} src="/static/logo128.png"></Avatar>
          <Divider></Divider>
          <form onSubmit={form.onSubmit(login)}>
            <Stack>
              <TextInput
                placeholder="Username"
                required
                {...form.getInputProps("username")}
              ></TextInput>
              <PasswordInput
                required
                placeholder="Password"
                {...form.getInputProps("password")}
              ></PasswordInput>
              <Divider></Divider>
              <Button fullWidth uppercase type="submit">
                Login
              </Button>
            </Stack>
          </form>
        </Stack>
      </Card>
    </Container>
  );
};

export default Authentication;
