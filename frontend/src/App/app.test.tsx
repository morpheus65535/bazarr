import { render } from "@/tests";
import { StrictMode } from "react";
import { describe, it } from "vitest";
import App from ".";

describe("App", () => {
  it("should render without crash", () => {
    render(
      <StrictMode>
        <App />
      </StrictMode>
    );
  });
});
