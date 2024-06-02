import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Router } from "./Router";
import { AllProviders } from "./providers";

const container = document.getElementById("root");

if (container === null) {
  Error("Cannot initialize app, root not found");
} else {
  const root = createRoot(container);
  root.render(
    <StrictMode>
      <AllProviders>
        <Router />
      </AllProviders>
    </StrictMode>,
  );
}
