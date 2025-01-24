import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import SystemReleasesView from ".";

describe("System Releases", () => {
  it("should render with releases", async () => {
    server.use(
      http.get("/api/system/releases", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<SystemReleasesView />);

    // TODO: Assert
  });
});
