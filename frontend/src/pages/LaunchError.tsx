import { Reload } from "@/utilities";
import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Alert, Button, Container } from "@mantine/core";
import { FunctionComponent } from "react";

interface Props {
  children: string;
}

const LaunchError: FunctionComponent<Props> = ({ children }) => (
  <Container className="my-3">
    <Alert
      className="d-flex flex-nowrap justify-content-between align-items-center"
      color="danger"
    >
      <div>
        <FontAwesomeIcon
          className="mr-2"
          icon={faExclamationTriangle}
        ></FontAwesomeIcon>
        <span>{children}</span>
      </div>
      <Button color="outline-danger" onClick={Reload}>
        Reload
      </Button>
    </Alert>
  </Container>
);

export default LaunchError;
