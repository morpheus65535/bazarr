import { describe } from "vitest";
import { render } from "@/tests";
import MovieMassEditor from "./Editor";
import MovieView from ".";

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
