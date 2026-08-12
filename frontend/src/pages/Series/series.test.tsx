import { http } from "msw";
import { HttpResponse } from "msw";
import { beforeEach, describe, it } from "vitest";
import { customRender } from "@/tests";
import server from "@/tests/mocks/node";
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
