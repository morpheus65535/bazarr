/* eslint-disable camelcase */

import { http } from "msw";
import { HttpResponse } from "msw";
import { render, screen } from "@/tests";
import server from "@/tests/mocks/node";
import WantedSeriesView from ".";

describe("Wanted Series", () => {
  it("should render with wanted series", async () => {
    const mockData = {
      data: [
        {
          sonarrSeriesId: 1,
          sonarrEpisodeId: 101,
          seriesTitle: "Breaking Bad",
          episode_number: "S01E01",
          episodeTitle: "Pilot",
          missing_subtitles: [
            {
              code2: "en",
              name: "English",
              hi: false,
              forced: false,
            },
          ],
        },
      ],
      total: 1,
      page: 1,
      per_page: 10,
    };

    server.use(
      http.get("/api/episodes/wanted", () => {
        return HttpResponse.json(mockData);
      }),
    );

    render(<WantedSeriesView />);

    await screen.findByText("Breaking Bad");
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Episode")).toBeInTheDocument();
    expect(screen.getByText("Missing")).toBeInTheDocument();
    expect(screen.getByText("Breaking Bad")).toBeInTheDocument();
    expect(screen.getByText("S01E01")).toBeInTheDocument();
    expect(screen.getByText("Pilot")).toBeInTheDocument();
  });

  it("should render empty state when no wanted series", async () => {
    server.use(
      http.get("/api/episodes/wanted", () => {
        return HttpResponse.json({
          data: [],
          total: 0,
          page: 1,
          per_page: 10,
        });
      }),
    );

    render(<WantedSeriesView />);

    await screen.findByText(/No missing Series subtitles/i);
  });
});
