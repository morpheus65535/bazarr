/* eslint-disable camelcase */

import { http } from "msw";
import { HttpResponse } from "msw";
import { render, screen } from "@/tests";
import server from "@/tests/mocks/node";
import WantedMoviesView from ".";

describe("Wanted Movies", () => {
  it("should render with wanted movies", async () => {
    const mockMovies = [
      {
        title: "The Shawshank Redemption",
        radarrId: 1,
        missing_subtitles: [
          {
            code2: "en",
            name: "English",
            hi: false,
            forced: false,
          },
        ],
      },
    ];

    server.use(
      http.get("/api/movies/wanted", () => {
        return HttpResponse.json({
          data: mockMovies,
        });
      }),
    );

    render(<WantedMoviesView />);

    const movieTitle = await screen.findByText("The Shawshank Redemption");
    expect(movieTitle).toBeInTheDocument();

    const movieLink = screen.getByRole("link", {
      name: "The Shawshank Redemption",
    });
    expect(movieLink).toHaveAttribute("href", "/movies/1");
  });

  it("should render empty state when no wanted movies", async () => {
    server.use(
      http.get("/api/movies/wanted", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<WantedMoviesView />);

    const table = await screen.findByRole("table");
    expect(table).toBeInTheDocument();

    const movieTitle = screen.queryByText("The Shawshank Redemption");
    expect(movieTitle).not.toBeInTheDocument();
  });
});
