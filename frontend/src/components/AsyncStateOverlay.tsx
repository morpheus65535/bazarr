import React, { PropsWithChildren } from "react";
import { LoadingIndicator } from ".";

interface Params<T> {
  state: AsyncState<T>;
  exist?: (item: T) => boolean;
  children?: (item: NonNullable<T>) => JSX.Element;
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

  if (state.updating && missing) {
    return <LoadingIndicator></LoadingIndicator>;
  } else if (state.items === null || state.items === undefined) {
    return null;
  } else {
    return (
      <React.Fragment>{children && children(state.items!)}</React.Fragment>
    );
  }
}

export default AsyncStateOverlay;
