import { faDizzy } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Button, Container } from "react-bootstrap";
import { GithubRepoRoot } from "../constants";
import { Reload } from "../utilities";

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
      <Button
        className="mx-1"
        href={`${GithubRepoRoot}/issues/new/choose`}
        target="_blank"
        variant="warning"
      >
        Report Issue
      </Button>
      <Button className="mx-1" onClick={Reload} variant="light">
        Reload Page
      </Button>
    </div>
  </Container>
);

export default UIError;
