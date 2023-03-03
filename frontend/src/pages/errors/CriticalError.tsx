import { Reload } from "@/utilities";
import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Alert, Container, Text } from "@mantine/core";
import { FunctionComponent } from "react";

interface Props {
  message: string;
}

const CriticalError: FunctionComponent<Props> = ({ message }) => (
  <Container my="xl">
    <Alert
      title="Something is wrong!"
      color="red"
      icon={<FontAwesomeIcon icon={faExclamationTriangle} />}
      withCloseButton
      closeButtonLabel="Reload"
      onClose={Reload}
    >
      <Text color="red">{message}</Text>
    </Alert>
  </Container>
);

export default CriticalError;
