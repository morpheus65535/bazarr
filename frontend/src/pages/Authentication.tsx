import { FunctionComponent } from "react";
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
import { useForm } from "@mantine/form";
import { useSystem } from "@/apis/hooks";
import { Environment } from "@/utilities";

const Authentication: FunctionComponent = () => {
  const { login } = useSystem();

  const form = useForm({
    initialValues: {
      username: "",
      password: "",
    },
  });

  return (
    <Container my="xl" size={400}>
      <Card shadow="xl">
        <Stack>
          <Avatar
            mx="auto"
            size={64}
            src={`${Environment.baseUrl}/images/logo128.png`}
          ></Avatar>
          <Divider></Divider>
          <form
            onSubmit={form.onSubmit((values) => {
              login(values);
            })}
          >
            <Stack>
              <TextInput
                name="Username"
                placeholder="Username"
                required
                {...form.getInputProps("username")}
              ></TextInput>
              <PasswordInput
                name="Password"
                required
                placeholder="Password"
                {...form.getInputProps("password")}
              ></PasswordInput>
              <Divider></Divider>
              <Button fullWidth tt="uppercase" type="submit">
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
