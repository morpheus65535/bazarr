import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { useRoutes } from "react-router-dom";
import { useRouteItems } from "./Router";
import { AllProviders } from "./providers";

const RouteApp = () => {
  const items = useRouteItems();

  return useRoutes(items);
};

const container = document.getElementById("root");

if (container === null) {
  Error("Cannot initialize app, root not found");
} else {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <AllProviders>
        <RouteApp />
      </AllProviders>
    </StrictMode>
  );
}
