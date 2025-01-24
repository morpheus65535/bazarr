import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import MoviesHistoryView from ".";

describe("History Movies", () => {
  it("should render with movies", async () => {
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

    render(<MoviesHistoryView />);

    // TODO: Assert
  });
});
