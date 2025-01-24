import { http } from "msw";
import { HttpResponse } from "msw";
import { render, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import BlacklistMoviesView from ".";

describe("Blacklist Movies", () => {
  it("should render with blacklisted movies", async () => {
    server.use(
      http.get("/api/movies/blacklist", () => {
        return HttpResponse.json({
          data: [
            {
              title: "Batman vs Teenage Mutant Ninja Turtles",
              radarrId: 50,
              provider: "yifysubtitles",
              subs_id:
                "https://yifysubtitles.ch/subtitles/batman-vs-teenage-mutant-ninja-turtles-2019-english-yify-19252",
              language: {
                name: "English",
                code2: "en",
                code3: "eng",
                forced: false,
                hi: false,
              },
              timestamp: "28 seconds ago",
              parsed_timestamp: "01/23/25 05:39:36",
            },
          ],
        });
      }),
    );

    render(<BlacklistMoviesView />);

    await waitFor(() => {
      expect(screen.getByText("yifysubtitles")).toBeInTheDocument();
    });
  });

  it("should render without blacklisted movies", async () => {
    server.use(
      http.get("/api/movies/blacklist", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<BlacklistMoviesView />);

    await waitFor(() => {
      expect(
        screen.getByText("No blacklisted movies subtitles"),
      ).toBeInTheDocument();
    });

    server.resetHandlers();
  });
});
