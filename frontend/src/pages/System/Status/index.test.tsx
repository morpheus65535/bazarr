import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import SystemStatusView from ".";

describe("System Status", () => {
  it("should render with status", async () => {
    server.use(
      http.get("/api/system/status", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    server.use(
      http.get("/api/system/health", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<SystemStatusView />);

    // TODO: Assert
  });
});
