import { http, HttpResponse } from "msw/http";
import { customRender, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import SportsHistoryView from ".";

const historyItem = {
  leagueTitle: "UFC",
  eventTitle: "UFC 300",
  partName: "Main Card",
  language: { code2: "en", name: "English" },
  action: 1,
  timestamp: "2026-11-25",
  parsed_timestamp: "Nov 25, 2026",
  sportarrLeagueId: 5,
  sportsEventId: 11,
  description: "Test description",
  score: "80.0%",
  matches: [],
  dont_matches: [],
  blacklisted: false,
};

const renderWith = (upgradable: boolean) => {
  server.use(
    http.get("/api/sports/history", () => {
      return HttpResponse.json({
        data: [{ ...historyItem, upgradable }],
        total: 1,
      });
    }),
  );

  customRender(<SportsHistoryView />);
};

const iconNames = () =>
  screen
    .queryAllByRole("img", { hidden: true })
    .map((icon) => icon.getAttribute("data-icon"));

describe("History Sports", () => {
  it("should mark an upgradable subtitle", async () => {
    renderWith(true);

    await waitFor(() => {
      expect(screen.getByText("UFC 300")).toBeInTheDocument();
    });

    expect(screen.getByText("Upgradable")).toBeInTheDocument();
    expect(iconNames()).toContain("recycle");
  });

  it("should not mark a subtitle that cannot be upgraded", async () => {
    renderWith(false);

    await waitFor(() => {
      expect(screen.getByText("UFC 300")).toBeInTheDocument();
    });

    expect(iconNames()).not.toContain("recycle");
  });
});
