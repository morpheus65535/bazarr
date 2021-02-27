import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { PropsWithChildren, useCallback } from "react";
import { Alert, Button, Container } from "react-bootstrap";
import { LoadingIndicator } from ".";

interface Params<T> {
  state: AsyncState<T>;
  exist?: (item: T) => boolean;
  children: (item: NonNullable<T>, error?: Error) => JSX.Element;
}

function defaultExist(item: any) {
  if (item instanceof Array) {
    return item.length !== 0;
  } else {
    return item !== null && item !== undefined;
  }
}

function AsyncStateOverlay<T>(props: PropsWithChildren<Params<T>>) {
  const { exist, state, children } = props;
  const missing = exist ? !exist(state.items) : !defaultExist(state.items);

  const reload = useCallback(() => {
    window.location.reload();
  }, []);

  if (state.updating) {
    if (missing) {
      return <LoadingIndicator></LoadingIndicator>;
    }
  } else {
    if (state.error && missing) {
      return (
        <Container>
          <Alert variant="danger" className="my-4">
            <Alert.Heading>
              <FontAwesomeIcon
                className="mr-2"
                icon={faExclamationTriangle}
              ></FontAwesomeIcon>
              <span>Ouch! You got an error</span>
            </Alert.Heading>
            <p>{state.error.message}</p>
            <hr></hr>
            <div className="d-flex justify-content-end">
              <Button variant="outline-danger" onClick={reload}>
                Reload
              </Button>
            </div>
          </Alert>
        </Container>
      );
    }
  }

  return children(state.items!, state.error);
}

export default AsyncStateOverlay;
