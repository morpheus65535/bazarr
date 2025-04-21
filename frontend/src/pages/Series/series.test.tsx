import { http } from "msw";
import { HttpResponse } from "msw";
import { beforeEach, describe, it } from "vitest";
import { customRender } from "@/tests";
import server from "@/tests/mocks/node";
import SeriesMassEditor from "./Editor";
import SeriesView from ".";

describe("Series page", () => {
  beforeEach(() => {
    server.use(
      http.get("/api/series", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );
  });

  it("should render", () => {
    customRender(<SeriesView />);
  });
});

describe("Series editor page", () => {
  beforeEach(() => {
    server.use(
      http.get("/api/series", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );
    server.use(
      http.get("/api/system/languages/profiles", () => {
        return HttpResponse.json([]);
      }),
    );
  });

  it("should render", () => {
    customRender(<SeriesMassEditor />);
  });
});
