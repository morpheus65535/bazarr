import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import SystemLogsView from ".";

describe("System Logs", () => {
  it("should render with logs", async () => {
    server.use(
      http.get("/api/system/logs", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<SystemLogsView />);

    // TODO: Assert
  });
});
