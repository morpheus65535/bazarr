import { AllProviders } from "@/providers";
import { render, RenderOptions } from "@testing-library/react";
import {
  FunctionComponent,
  PropsWithChildren,
  ReactElement,
  StrictMode,
} from "react";

const AllProvidersWithStrictMode: FunctionComponent<PropsWithChildren> = ({
  children,
}) => {
  return (
    <StrictMode>
      <AllProviders>{children}</AllProviders>
    </StrictMode>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) => render(ui, { wrapper: AllProvidersWithStrictMode, ...options });

// re-export everything
export * from "@testing-library/react";
// override render method
export { customRender as render };
export { render as rawRender };
