import { http } from "msw";
import { HttpResponse } from "msw";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import WantedMoviesView from "./Movies";
import WantedSeriesView from "./Series";

const cases: RenderTestCase[] = [
  {
    name: "movie page",
    ui: WantedMoviesView,
    setupEach: () => {
      server.use(
        http.get("/api/movies/wanted", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "series page",
    ui: WantedSeriesView,
    setupEach: () => {
      server.use(
        http.get("/api/episodes/wanted", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
];

renderTest("Wanted", cases);
