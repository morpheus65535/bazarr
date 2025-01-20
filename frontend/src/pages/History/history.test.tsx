import { http } from "msw";
import { HttpResponse } from "msw";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import HistoryStats from "./Statistics/HistoryStats";
import MoviesHistoryView from "./Movies";
import SeriesHistoryView from "./Series";

const cases: RenderTestCase[] = [
  {
    name: "movie page",
    ui: MoviesHistoryView,
    setupEach: () => {
      server.use(
        http.get("/api/movies/history", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
      server.use(
        http.get("/api/providers", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
      server.use(
        http.get("/api/system/languages", () => {
          return HttpResponse.json({});
        }),
      );
    },
  },
  {
    name: "series page",
    ui: SeriesHistoryView,
    setupEach: () => {
      server.use(
        http.get("/api/episodes/history", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "statistics page",
    ui: HistoryStats,
    setupEach: () => {
      server.use(
        http.get("/api/history/stats", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
];

renderTest("History", cases);
