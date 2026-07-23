import { FunctionComponent, useMemo } from "react";
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
import { faDizzy } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { GithubRepoRoot } from "@/constants";
import { Reload } from "@/utilities";

const Placeholder = "********";

interface Props {
  error: Error;
}

const UIError: FunctionComponent<Props> = ({ error }) => {
  const stack = useMemo(() => {
    const callStack = (error.stack ?? "").replaceAll(
      window.location.host,
      Placeholder,
    );

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
      <Group justify="center">
        <Anchor href={`${GithubRepoRoot}/issues/new/choose`} target="_blank">
          <Button color="warning">Report Issue</Button>
        </Anchor>
        <Button onClick={Reload}>Reload Page</Button>
      </Group>
    </Container>
  );
};

export default UIError;
