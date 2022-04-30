import { render } from "@testing-library/react";
import { describe, it } from "vitest";
import { Entrance } from "../src";

describe("render test", () => {
  it("render without crashing", () => {
    render(<Entrance />);
  });
});
