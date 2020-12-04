import React, { PropsWithChildren } from "react";
import { LoadingOverlay } from ".";

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
      return <LoadingOverlay></LoadingOverlay>;
    } else {
      return <React.Fragment>{children}</React.Fragment>;
    }
  }
}

export default AsyncStateOverlay;
