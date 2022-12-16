import { render } from "@testing-library/react";
import { StrictMode } from "react";
import { describe, it } from "vitest";
import { Main } from "../src/main";

describe("App", () => {
  it("should render without crash", () => {
    render(
      <StrictMode>
        <Main />
      </StrictMode>
    );
  });
});
