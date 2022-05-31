import { LoadingOverlay } from "@mantine/core";
import { FunctionComponent, Suspense } from "react";

const Lazy: FunctionComponent = ({ children }) => {
  return <Suspense fallback={<LoadingOverlay visible />}>{children}</Suspense>;
};

export default Lazy;
