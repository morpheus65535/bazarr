import { render } from "@testing-library/react";
import { StrictMode } from "react";
import { describe, it } from "vitest";
import { Main } from "../src/main";

describe("render test", () => {
  it("render without crashing", () => {
    render(
      <StrictMode>
        <Main />
      </StrictMode>
    );
  });
});
