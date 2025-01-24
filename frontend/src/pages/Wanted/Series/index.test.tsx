import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import WantedSeriesView from ".";

describe("Wanted Series", () => {
  it("should render with wanted series", async () => {
    server.use(
      http.get("/api/episodes/wanted", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<WantedSeriesView />);

    // TODO: Assert
  });
});
