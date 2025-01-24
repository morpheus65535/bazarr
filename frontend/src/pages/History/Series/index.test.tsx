import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import SeriesHistoryView from ".";

describe("History Series", () => {
  it("should render with series", async () => {
    server.use(
      http.get("/api/episodes/history", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<SeriesHistoryView />);

    // TODO: Assert
  });
});
