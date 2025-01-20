import { http } from "msw";
import { HttpResponse } from "msw";
import { beforeEach, describe, it } from "vitest";
import { render } from "@/tests";
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
    render(<SeriesView />);
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
    render(<SeriesMassEditor />);
  });
});
