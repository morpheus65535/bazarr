import { Reload } from "@/utilities";
import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { FunctionComponent } from "react";
import { Alert, Button, Container } from "react-bootstrap";

interface Props {
  children: string;
}

const LaunchError: FunctionComponent<Props> = ({ children }) => (
  <Container className="my-3">
    <Alert
      className="d-flex flex-nowrap justify-content-between align-items-center"
      variant="danger"
    >
      <div>
        <FontAwesomeIcon
          className="mr-2"
          icon={faExclamationTriangle}
        ></FontAwesomeIcon>
        <span>{children}</span>
      </div>
      <Button variant="outline-danger" onClick={Reload}>
        Reload
      </Button>
    </Alert>
  </Container>
);

export default LaunchError;
