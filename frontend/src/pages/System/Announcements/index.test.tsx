import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import SystemAnnouncementsView from ".";

describe("System Announcements", () => {
  it("should render with announcements", async () => {
    server.use(
      http.get("/api/system/announcements", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<SystemAnnouncementsView />);

    // TODO: Assert
  });
});
