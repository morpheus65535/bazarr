/* eslint-disable camelcase */
import { http } from "msw";
import { HttpResponse } from "msw";
import { render, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import BlacklistSeriesView from ".";

describe("Blacklist Series", () => {
  it("should render without blacklisted series", async () => {
    server.use(
      http.get("/api/episodes/blacklist", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<BlacklistSeriesView />);

    await waitFor(() => {
      expect(
        screen.getByText("No blacklisted series subtitles"),
      ).toBeInTheDocument();
    });
  });

  it("should render with blacklisted series", async () => {
    server.use(
      http.get("/api/episodes/blacklist", () => {
        // TODO: Replace with Factory
        return HttpResponse.json({
          data: [
            {
              seriesTitle: "Dragon Ball DAIMA",
              episode_number: "1x14",
              episodeTitle: "Taboo",
              sonarrSeriesId: 56,
              provider: "animetosho",
              subs_id:
                "https://animetosho.org/storage/attach/0022fd50/2293072.xz",
              language: {
                name: "English",
                code2: "en",
                code3: "eng",
                forced: false,
                hi: false,
              },
              timestamp: "now",
              parsed_timestamp: "01/24/25 01:38:03",
            },
          ],
        });
      }),
    );

    render(<BlacklistSeriesView />);

    await waitFor(() => {
      expect(screen.getByText("animetosho")).toBeInTheDocument();
    });
  });
});
