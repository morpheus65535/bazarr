import { GithubRepoRoot } from "@/constants";
import { Reload } from "@/utilities";
import { faDizzy } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Anchor,
  Box,
  Button,
  Center,
  Container,
  Group,
  Text,
  Title,
} from "@mantine/core";
import { FunctionComponent } from "react";

interface Props {
  error: Error;
}

const UIError: FunctionComponent<Props> = ({ error }) => (
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
    <Center>
      <Text mb="lg">{error.message}</Text>
    </Center>
    <Group position="center">
      <Anchor href={`${GithubRepoRoot}/issues/new/choose`} target="_blank">
        <Button color="yellow">Report Issue</Button>
      </Anchor>
      <Button className="mx-1" onClick={Reload} color="light">
        Reload Page
      </Button>
    </Group>
  </Container>
);

export default UIError;
