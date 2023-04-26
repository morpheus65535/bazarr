import { LoadingOverlay } from "@mantine/core";
import { FunctionComponent, PropsWithChildren, Suspense } from "react";

const Lazy: FunctionComponent<PropsWithChildren> = ({ children }) => {
  return <Suspense fallback={<LoadingOverlay visible />}>{children}</Suspense>;
};

export default Lazy;
