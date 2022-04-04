import { FunctionComponent, ReactElement, useEffect, useState } from "react";
import { UseQueryResult } from "react-query";
import { LoadingIndicator } from ".";

interface QueryOverlayProps {
  result: UseQueryResult<unknown, unknown>;
  children: ReactElement;
}

export const QueryOverlay: FunctionComponent<QueryOverlayProps> = ({
  children,
  result: { isLoading, isError, error },
}) => {
  if (isLoading) {
    return <LoadingIndicator></LoadingIndicator>;
  } else if (isError) {
    return <p>{error as string}</p>;
  }

  return children;
};

interface PromiseProps<T> {
  promise: () => Promise<T>;
  children: FunctionComponent<T>;
}

export function PromiseOverlay<T>({ promise, children }: PromiseProps<T>) {
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
