import { FunctionComponent } from "react";
import { HttpResponse } from "msw";
import { http } from "msw";
import server from "./mocks/node";
import { render } from ".";

export interface RenderTestCase {
  name: string;
  ui: FunctionComponent;
}

export function renderTest(name: string, cases: RenderTestCase[]) {
  describe(name, () => {
    beforeEach(() => {
      server.use(
        http.get("/api/movies/history", () => {
          return HttpResponse.json({});
        }),
        http.get("/api/episodes/history", () => {
          return HttpResponse.json({});
        }),
        http.get("/api/system/searches", () => {
          return HttpResponse.json({});
        }),
        http.get("/api/providers", () => {
          return HttpResponse.json({
            data: [
              {
                name: "Provider 1",
                retry: "-",
                status: "History",
              },
            ],
          });
        }),
        http.get("/api/system/languages", () => {
          return HttpResponse.json({});
        }),
        http.get("/api/history/stats", () => {
          return HttpResponse.json({
            movies: [
              {
                date: "2025-01-17",
                count: 1,
              },
            ],
            series: [
              {
                date: "2025-01-17",
                count: 1,
              },
            ],
          });
        }),
      );
    });

    cases.forEach((element) => {
      it(`${element.name.toLowerCase()} should render`, () => {
        render(<element.ui />);
      });
    });
  });
}
