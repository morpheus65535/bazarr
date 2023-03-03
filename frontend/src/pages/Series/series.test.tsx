import { render } from "@/tests";
import { describe } from "vitest";
import SeriesView from ".";
import SeriesMassEditor from "./Editor";

describe("Series page", () => {
  it("should render", () => {
    render(<SeriesView />);
  });
});

describe("Series editor page", () => {
  it("should render", () => {
    render(<SeriesMassEditor />);
  });
});
