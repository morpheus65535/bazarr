import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import SystemTasksView from ".";

describe("System Tasks", () => {
  it("should render with tasks", async () => {
    server.use(
      http.get("/api/system/tasks", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<SystemTasksView />);

    // TODO: Assert
  });
});
