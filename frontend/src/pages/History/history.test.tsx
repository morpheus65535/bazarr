import { renderTest, RenderTestCase } from "@/tests/render";
import MoviesHistoryView from "./Movies";
import SeriesHistoryView from "./Series";
import HistoryStats from "./Statistics";

const cases: RenderTestCase[] = [
  {
    name: "movie page",
    ui: MoviesHistoryView,
  },
  {
    name: "series page",
    ui: SeriesHistoryView,
  },
  {
    name: "statistics page",
    ui: HistoryStats,
  },
];

renderTest("History", cases);
