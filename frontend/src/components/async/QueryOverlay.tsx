import { FunctionComponent, ReactNode } from "react";
import { LoadingOverlay } from "@mantine/core";
import { UseQueryResult } from "@tanstack/react-query";
import { LoadingProvider } from "@/contexts";

interface QueryOverlayProps {
  result: UseQueryResult<unknown, unknown>;
  global?: boolean;
  children: ReactNode;
}

const QueryOverlay: FunctionComponent<QueryOverlayProps> = ({
  children,
  global = false,
  result: { isLoading },
}) => {
  return (
    <LoadingProvider value={isLoading}>
      <LoadingOverlay visible={global && isLoading}></LoadingOverlay>
      {children}
    </LoadingProvider>
  );
};

export default QueryOverlay;
