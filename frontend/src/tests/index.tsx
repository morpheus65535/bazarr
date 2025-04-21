import {
  FunctionComponent,
  PropsWithChildren,
  ReactElement,
  StrictMode,
} from "react";
import { createBrowserRouter, RouteObject, RouterProvider } from "react-router";
import { render, RenderOptions } from "@testing-library/react";
import { AllProviders } from "@/providers";

const AllProvidersWithStrictMode: FunctionComponent<PropsWithChildren> = ({
  children,
}) => {
  const route: RouteObject = {
    path: "/",
    element: children,
  };

  // TODO: Update router system
  const router = createBrowserRouter([route]);

  return (
    <StrictMode>
      <AllProviders>
        <RouterProvider router={router} />
      </AllProviders>
    </StrictMode>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: AllProvidersWithStrictMode, ...options });

// re-export everything
export * from "@testing-library/react";

// override render method
export { customRender };
export { render as rawRender };
