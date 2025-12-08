import { http } from "msw";
import { HttpResponse } from "msw";
import { describe, it } from "vitest";
import { customRender } from "@/tests";
import server from "@/tests/mocks/node";
import App from ".";

describe("App", () => {
  it("should render without crash", () => {
    server.use(
      http.get("/api/system/searches", () => {
        return HttpResponse.json({});
      }),
    );

    server.use(
      http.get("/api/system/jobs", () => {
        return HttpResponse.json({});
      }),
    );

    customRender(<App />);
  });
});
