import { renderTest, RenderTestCase } from "@/tests/render";
import WantedMoviesView from "./Movies";
import WantedSeriesView from "./Series";

const cases: RenderTestCase[] = [
  {
    name: "movie page",
    ui: WantedMoviesView,
  },
  {
    name: "series page",
    ui: WantedSeriesView,
  },
];

renderTest("Wanted", cases);
