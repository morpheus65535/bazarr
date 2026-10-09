import { FunctionComponent } from "react";
import { Alert, Container, Text } from "@mantine/core";
import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Reload } from "@/utilities";

interface Props {
  message: string;
}

const CriticalError: FunctionComponent<Props> = ({ message }) => (
  <Container my="xl">
    <Alert
      title="Something is wrong!"
      color="danger"
      icon={<FontAwesomeIcon icon={faExclamationTriangle} />}
      withCloseButton
      closeButtonLabel="Reload"
      onClose={Reload}
    >
      <Text c="danger">{message}</Text>
    </Alert>
  </Container>
);

export default CriticalError;
