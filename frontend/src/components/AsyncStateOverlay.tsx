import React from "react";
import { LoadingOverlay } from ".";

interface Params<T> {
  state: AsyncState<T>;
  exist?: (item: T) => boolean;
  children?: (item: NonNullable<T>) => JSX.Element;
}

function defaultExist<T>(item: T) {
  if (item instanceof Array) {
    return item.length !== 0;
  } else {
    return item !== null && item !== undefined;
  }
}

class AsyncStateOverlay<T> extends React.Component<Params<T>> {
  render() {
    const { exist, state, children } = this.props;
    const missing = exist ? !exist(state.items) : !defaultExist(state.items);

    if (state.updating) {
      return <LoadingOverlay></LoadingOverlay>;
    } else if (missing) {
      return null;
    } else {
      return (
        <React.Fragment>{children && children(state.items!)}</React.Fragment>
      );
    }
  }
}

export default AsyncStateOverlay;
