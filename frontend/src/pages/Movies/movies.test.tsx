import { render } from "@/tests";
import MovieMassEditor from "./Editor";
import MovieView from ".";

import { describe } from "vitest";

describe("Movies page", () => {
  it("should render", () => {
    render(<MovieView />);
  });
});

describe("Movies editor page", () => {
  it("should render", () => {
    render(<MovieMassEditor />);
  });
});
