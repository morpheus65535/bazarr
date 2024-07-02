import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { AllProviders } from "./providers";
import { Router } from "./Router";

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
