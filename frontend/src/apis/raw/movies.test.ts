import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import api from "@/apis/raw";
import server from "@/tests/mocks/node";

describe("MovieApi", () => {
  describe("action", () => {
    it.each([
      ["search-missing", 1],
      ["scan-disk", 2],
      ["sync", 3],
    ] as const)("sends radarrid for '%s' action", async (action, radarrId) => {
      let capturedBody: FormData | null = null;

      server.use(
        http.patch("/api/movies", async ({ request }) => {
          capturedBody = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.movies.action({ action, radarrId });

      expect(capturedBody).not.toBeNull();
      expect(capturedBody!.get("action")).toBe(action);
      expect(capturedBody!.get("radarrid")).toBe(String(radarrId));
      expect(capturedBody!.get("radarr_id")).toBeNull();
    });

    it("does not send radarrid for search-wanted action", async () => {
      let capturedBody: FormData | null = null;

      server.use(
        http.patch("/api/movies", async ({ request }) => {
          capturedBody = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.movies.action({ action: "search-wanted" });

      expect(capturedBody).not.toBeNull();
      expect(capturedBody!.get("action")).toBe("search-wanted");
      expect(capturedBody!.get("radarrid")).toBeNull();
    });
  });
});
