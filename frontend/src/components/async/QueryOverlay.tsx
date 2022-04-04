import { FunctionComponent, ReactElement } from "react";
import { UseQueryResult } from "react-query";
import { LoadingIndicator } from "..";

interface QueryOverlayProps {
  result: UseQueryResult<unknown, unknown>;
  children: ReactElement;
}

const QueryOverlay: FunctionComponent<QueryOverlayProps> = ({
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

export default QueryOverlay;
