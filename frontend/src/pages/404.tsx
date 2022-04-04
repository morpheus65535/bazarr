import { faEyeSlash as fasEyeSlash } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Container } from "@mantine/core";
import { FunctionComponent } from "react";

const NotFound: FunctionComponent = () => {
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

export default NotFound;
