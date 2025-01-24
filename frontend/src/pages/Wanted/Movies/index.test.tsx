import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import WantedMoviesView from ".";

describe("Wanted Movies", () => {
  it("should render with wanted movies", async () => {
    server.use(
      http.get("/api/movies/wanted", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<WantedMoviesView />);

    // TODO: Assert
  });
});
