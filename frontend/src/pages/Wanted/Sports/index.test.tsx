import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw/http";
import { customRender, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import WantedSportsView from ".";

describe("Wanted Sports", () => {
  it("links the league and searches one missing language", async () => {
    const searches: { params: URLSearchParams; body: FormData }[] = [];

    server.use(
      http.get("/api/sports/wanted", () => {
        return HttpResponse.json({
          data: [
            {
              leagueTitle: "UFC",
              eventTitle: "UFC 300",
              partName: "Main Card",
              sportarrLeagueId: 4,
              sportsEventId: 12,
              sceneName: null,
              tags: [],
              sport: "Fighting",
              missing_subtitles: [
                {
                  code2: "en",
                  name: "English",
                  hi: true,
                  forced: false,
                },
              ],
            },
          ],
          total: 1,
        });
      }),
      // The API client sends the form as multipart form data, not JSON.
      http.patch("/api/sports/subtitles", async ({ request }) => {
        searches.push({
          params: new URL(request.url).searchParams,
          body: await request.formData(),
        });
        return new HttpResponse(null, { status: 204 });
      }),
    );

    customRender(<WantedSportsView />);

    const leagueLink = await screen.findByRole("link", { name: "UFC" });
    expect(leagueLink).toHaveAttribute("href", "/sports/4");

    await userEvent.click(screen.getByText(/^en/));

    await waitFor(() => expect(searches).toHaveLength(1));
    const { params, body } = searches[0];
    expect(params.get("leagueid")).toBe("4");
    expect(params.get("eventid")).toBe("12");
    expect(body.get("language")).toBe("en");
    expect(body.get("hi")).toBe("true");
    expect(body.get("forced")).toBe("false");
  });
});
