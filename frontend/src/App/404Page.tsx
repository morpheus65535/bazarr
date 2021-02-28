import { faEyeSlash as fasEyeSlash } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { FunctionComponent } from "react";
import { Container } from "react-bootstrap";

const EmptyPage: FunctionComponent = () => {
  return (
    <Container className="d-flex flex-column align-items-center my-5">
      <h1>
        <FontAwesomeIcon className="mr-2" icon={fasEyeSlash}></FontAwesomeIcon>
        404
      </h1>
      <p>The Request URL No Found</p>
    </Container>
  );
};

export default EmptyPage;
