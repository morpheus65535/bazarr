import { LoadingProvider } from "@/contexts";
import { LoadingOverlay } from "@mantine/core";
import { FunctionComponent, ReactNode } from "react";
import { UseQueryResult } from "react-query";

interface QueryOverlayProps {
  result: UseQueryResult<unknown, unknown>;
  global?: boolean;
  children: ReactNode;
}

const QueryOverlay: FunctionComponent<QueryOverlayProps> = ({
  children,
  global = false,
  result: { isLoading, isError, error },
}) => {
  return (
    <LoadingProvider value={isLoading}>
      <LoadingOverlay visible={global && isLoading}></LoadingOverlay>
      {children}
    </LoadingProvider>
  );
};

export default QueryOverlay;
