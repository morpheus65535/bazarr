import { FunctionComponent, PropsWithChildren, Suspense } from "react";
import { LoadingOverlay } from "@mantine/core";

const Lazy: FunctionComponent<PropsWithChildren> = ({ children }) => {
  return <Suspense fallback={<LoadingOverlay visible />}>{children}</Suspense>;
};

export default Lazy;
