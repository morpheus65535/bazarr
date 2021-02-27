import { faExclamation } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { PropsWithChildren, useCallback } from "react";
import { Button } from "react-bootstrap";
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
        <div className="d-flex flex-column w-100 align-items-center my-4">
          <FontAwesomeIcon size="lg" icon={faExclamation}></FontAwesomeIcon>
          <span className="my-2">{state.error.message}</span>
          <Button onClick={reload}>Reload</Button>
        </div>
      );
    }
  }

  return children(state.items!, state.error);
}

export default AsyncStateOverlay;
