import { http } from "msw";
import { HttpResponse } from "msw";
import { beforeEach, describe, it } from "vitest";
import { customRender } from "@/tests";
import server from "@/tests/mocks/node";
import MovieView from ".";

describe("Movies page", () => {
  beforeEach(() => {
    server.use(
      http.get("/api/movies", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );
  });

  it("should render", () => {
    customRender(<MovieView />);
  });
});
