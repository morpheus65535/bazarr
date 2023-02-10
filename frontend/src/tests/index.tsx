import { AllProviders } from "@/providers";
import { render, RenderOptions } from "@testing-library/react";
import { ReactElement } from "react";

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) => render(ui, { wrapper: AllProviders, ...options });

// re-export everything
export * from "@testing-library/react";
// override render method
export { customRender as render };
