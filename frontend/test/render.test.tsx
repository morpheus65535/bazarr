import { render } from "@testing-library/react";
import { StrictMode } from "react";
import { describe, it, vitest } from "vitest";
import { Main } from "../src/main";

describe("render test", () => {
  beforeAll(() => {
    // From https://stackoverflow.com/questions/39830580/jest-test-fails-typeerror-window-matchmedia-is-not-a-function
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vitest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vitest.fn(), // Deprecated
        removeListener: vitest.fn(), // Deprecated
        addEventListener: vitest.fn(),
        removeEventListener: vitest.fn(),
        dispatchEvent: vitest.fn(),
      })),
    });
  });

  it("render without crashing", () => {
    render(
      <StrictMode>
        <Main />
      </StrictMode>
    );
  });
});
