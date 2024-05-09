import { render } from "@/tests";
import SeriesMassEditor from "./Editor";
import SeriesView from ".";

import { describe } from "vitest";

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
