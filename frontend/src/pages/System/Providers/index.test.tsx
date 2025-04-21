import { http } from "msw";
import { HttpResponse } from "msw";
import { customRender } from "@/tests";
import server from "@/tests/mocks/node";
import SystemProvidersView from ".";

describe("System Providers", () => {
  it("should render with providers", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    customRender(<SystemProvidersView />);

    // TODO: Assert
  });
});
