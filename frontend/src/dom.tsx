import { StrictMode } from "react";
import ReactDOM from "react-dom";
import { useRoutes } from "react-router-dom";
import { AllProviders } from "./providers";
import { useRouteItems } from "./Router";

const RouteApp = () => {
  const items = useRouteItems();

  return useRoutes(items);
};

ReactDOM.render(
  <StrictMode>
    <AllProviders>
      <RouteApp />
    </AllProviders>
  </StrictMode>,
  document.getElementById("root")
);
