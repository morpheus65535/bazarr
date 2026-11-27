import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw/http";
import { beforeEach, describe, expect, it } from "vitest";
import { customRender, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import SportsView from ".";

describe("Sports page", () => {
  beforeEach(() => {
    window.localStorage.clear();
    server.use(
      http.get("/api/sports/leagues", () => {
        return HttpResponse.json({
          data: [
            {
              sportarrLeagueId: 4,
              externalId: "lg-4",
              title: "UFC",
              sortTitle: "ufc",
              sport: "Fighting",
              path: "/sports/UFC",
              poster: "",
              fanart: "",
              overview: "",
              monitored: false,
              profileId: null,
              tags: [],
              audio_language: [],
              created_at_timestamp: null,
              alternativeTitles: [],
              episodeFileCount: 2,
              episodeMissingCount: 0,
            },
          ],
          total: 1,
        });
      }),
      http.get("/api/sports/leagues/tags", () => {
        return HttpResponse.json({ data: [] });
      }),
    );
  });

  it("shows a tooltip on the monitored icon in the table", async () => {
    const { container } = customRender(<SportsView />);

    await screen.findByRole("link", { name: "UFC" });

    // The icon is decorative, so no role query reaches it.
    // eslint-disable-next-line testing-library/no-container, testing-library/no-node-access
    const icon = container.querySelector('[data-icon="bookmark"]');
    expect(icon).not.toBeNull();

    // The monitored filter also shows the word, so count the new one.
    const before = screen.queryAllByText("Unmonitored").length;
    await userEvent.hover(icon!);

    await waitFor(() =>
      expect(screen.queryAllByText("Unmonitored")).toHaveLength(before + 1),
    );
  });
});
