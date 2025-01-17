import { http } from "msw";
import { HttpResponse } from "msw";
import { describe, it } from "vitest";
import { render } from "@/tests";
import server from "@/tests/mocks/node";
import App from ".";

describe("App", () => {
  it("should render without crash", () => {
    server.use(
      http.get("/api/system/searches", () => {
        return HttpResponse.json({});
      }),
    );

    render(<App />);
  });
});
