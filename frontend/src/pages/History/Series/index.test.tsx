/* eslint-disable camelcase */

import { http } from "msw";
import { HttpResponse } from "msw";
import { customRender, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import SeriesHistoryView from ".";

describe("History Series", () => {
  it("should render with series", async () => {
    server.use(
      http.get("/api/episodes/history", () => {
        return HttpResponse.json({
          data: [
            {
              seriesTitle: "Breaking Bad",
              episode_number: "S05E07",
              episodeTitle: "Pilot",
              language: { code2: "en", name: "English" },
              action: "download",
              timestamp: "2023-05-10",
              parsed_timestamp: "May 10, 2023",
              sonarrSeriesId: 123,
              sonarrEpisodeId: 456,
              description: "Test description",
              score: 100,
              matches: [],
              dont_matches: [],
              upgradable: false,
              blacklisted: false,
            },
          ],
          page: 1,
          totalPages: 1,
          totalItems: 1,
        });
      }),
    );

    customRender(<SeriesHistoryView />);

    await waitFor(() => {
      expect(screen.getByText("Breaking Bad")).toBeInTheDocument();
    });

    expect(screen.getByText("S05E07")).toBeInTheDocument();
  });
});
