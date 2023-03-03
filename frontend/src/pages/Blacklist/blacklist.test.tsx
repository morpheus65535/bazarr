import { renderTest, RenderTestCase } from "@/tests/render";
import BlacklistMoviesView from "./Movies";
import BlacklistSeriesView from "./Series";

const cases: RenderTestCase[] = [
  {
    name: "movie page",
    ui: BlacklistMoviesView,
  },
  {
    name: "series page",
    ui: BlacklistSeriesView,
  },
];

renderTest("Blacklist", cases);
