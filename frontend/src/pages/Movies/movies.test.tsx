import { render } from "@/tests";
import { describe } from "vitest";
import MovieView from ".";
import MovieMassEditor from "./Editor";

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
