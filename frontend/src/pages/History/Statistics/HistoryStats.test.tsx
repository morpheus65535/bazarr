import { http } from "msw";
import { HttpResponse } from "msw";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import HistoryStats from "./HistoryStats";

describe("History Stats", () => {
  it("should render without stats", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );
    server.use(
      http.get("/api/system/languages", () => {
        return HttpResponse.json({});
      }),
    );
    server.use(
      http.get("/api/history/stats", () => {
        return HttpResponse.json({
          series: [],
        });
      }),
    );

    server.use(
      http.get("/api/system/providers", () => {
        return HttpResponse.json({});
      }),
    );

    render(<HistoryStats />);
  });
});
