import { GithubRepoRoot } from "@/constants";
import { Reload } from "@/utilities";
import { faDizzy } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Anchor,
  Box,
  Button,
  Center,
  Code,
  Container,
  Group,
  Text,
  Title,
} from "@mantine/core";
import { FunctionComponent, useMemo } from "react";

const Placeholder = "********";

interface Props {
  error: Error;
}

const UIError: FunctionComponent<Props> = ({ error }) => {
  const stack = useMemo(() => {
    let callStack = error.stack ?? "";

    // Remove sensitive information from the stack
    callStack = callStack.replaceAll(window.location.host, Placeholder);

    return callStack;
  }, [error.stack]);
  return (
    <Container my="lg">
      <Center>
        <Title>
          <Box component="span" mr="md">
            <FontAwesomeIcon icon={faDizzy}></FontAwesomeIcon>
          </Box>
          <Text component="span" inherit>
            Oops! UI is crashed!
          </Text>
        </Title>
      </Center>
      <Center my="xl">
        <Code>{stack}</Code>
      </Center>
      <Group position="center">
        <Anchor href={`${GithubRepoRoot}/issues/new/choose`} target="_blank">
          <Button color="yellow">Report Issue</Button>
        </Anchor>
        <Button onClick={Reload} color="light">
          Reload Page
        </Button>
      </Group>
    </Container>
  );
};

export default UIError;
