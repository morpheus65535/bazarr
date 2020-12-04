import React, { FunctionComponent, PropsWithChildren } from "react";
import { Spinner } from "react-bootstrap";

interface Params<T> {
  state: AsyncState<T>;
  exist?: (item: T) => boolean;
}

function defaultExist<T>(item: T) {
  if (item instanceof Array) {
    return item.length !== 0;
  } else {
    return item !== null || item !== undefined;
  }
}

class AsyncStateOverlay<T> extends React.Component<
  PropsWithChildren<Params<T>>
> {
  render() {
    const { state, children, exist } = this.props;

    const missing = exist ? !exist(state.items) : !defaultExist(state.items);

    if (state.updating && missing) {
      return (
        <div className="d-flex justify-content-center my-5">
          <Spinner animation="border"></Spinner>
        </div>
      );
    } else {
      return <React.Fragment>{children}</React.Fragment>;
    }
  }
}

export default AsyncStateOverlay;
