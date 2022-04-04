import { render } from "@testing-library/react";
import { describe, it } from "vitest";
import { Main } from "../src/main";

describe("render test", () => {
  it("render without crashing", () => {
    render(<Main />);
  });
});
