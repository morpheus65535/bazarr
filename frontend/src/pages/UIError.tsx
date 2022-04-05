import { GithubRepoRoot } from "@/constants";
import { Reload } from "@/utilities";
import { faDizzy } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Anchor, Button, Container } from "@mantine/core";
import { FunctionComponent } from "react";

interface Props {
  error: Error;
}

const UIError: FunctionComponent<Props> = ({ error }) => (
  <Container className="d-flex flex-column align-items-center my-5">
    <h1>
      <FontAwesomeIcon className="mr-2" icon={faDizzy}></FontAwesomeIcon>
      Oops! UI is crashed!
    </h1>
    <p>{error.message}</p>
    <div className="d-flex flex-row">
      <Anchor href={`${GithubRepoRoot}/issues/new/choose`} target="_blank">
        <Button color="yellow">Report Issue</Button>
      </Anchor>
      <Button className="mx-1" onClick={Reload} color="light">
        Reload Page
      </Button>
    </div>
  </Container>
);

export default UIError;
