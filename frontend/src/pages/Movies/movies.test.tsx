import { http } from "msw";
import { HttpResponse } from "msw";
import { beforeEach, describe, it } from "vitest";
import { customRender, screen } from "@/tests";
import server from "@/tests/mocks/node";
import MovieMassEditor from "./Editor";
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

describe("Movies editor page", () => {
  beforeEach(() => {
    server.use(
      http.get("/api/movies", () => {
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
    customRender(<MovieMassEditor />);

    expect(screen.getByText("Actions")).toBeInTheDocument();
  });
});
