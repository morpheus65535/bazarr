import { http } from "msw";
import { HttpResponse } from "msw";
import { beforeEach, describe, it } from "vitest";
import { render, screen } from "@/tests";
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
    render(<MovieView />);
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
    render(<MovieMassEditor />);

    expect(screen.getByText("Actions")).toBeInTheDocument();
  });
});
