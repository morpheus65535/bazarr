import { FunctionComponent, useEffect, useState } from "react";
import { LoadingIndicator } from "..";

interface PromiseProps<T> {
  promise: () => Promise<T>;
  children: FunctionComponent<T>;
}

function PromiseOverlay<T>({ promise, children }: PromiseProps<T>) {
  const [item, setItem] = useState<T | null>(null);

  useEffect(() => {
    promise().then(setItem);
  }, [promise]);

  if (item === null) {
    return <LoadingIndicator></LoadingIndicator>;
  } else {
    return children(item);
  }
}

export default PromiseOverlay;
