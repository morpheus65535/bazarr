import { http } from "msw";
import { HttpResponse } from "msw";
import server from "@/tests/mocks/node";
import { renderTest, RenderTestCase } from "@/tests/render";
import BlacklistMoviesView from "./Movies";
import BlacklistSeriesView from "./Series";

const cases: RenderTestCase[] = [
  {
    name: "movie page",
    ui: BlacklistMoviesView,
    setupEach: () => {
      server.use(
        http.get("/api/movies/blacklist", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
  {
    name: "series page",
    ui: BlacklistSeriesView,
    setupEach: () => {
      server.use(
        http.get("/api/episodes/blacklist", () => {
          return HttpResponse.json({
            data: [],
          });
        }),
      );
    },
  },
];

renderTest("Blacklist", cases);
