import { FunctionComponent, Suspense } from "react";
import { LoadingIndicator } from ".";

const Lazy: FunctionComponent = ({ children }) => {
  return <Suspense fallback={<LoadingIndicator />}>{children}</Suspense>;
};

export default Lazy;
