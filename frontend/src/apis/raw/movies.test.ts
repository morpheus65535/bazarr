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
      const capturedBody = { current: null as FormData | null };

      server.use(
        http.patch("/api/movies", async ({ request }) => {
          capturedBody.current = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.movies.action({ action, radarrId });

      expect(capturedBody.current).not.toBeNull();
      expect(capturedBody.current!.get("action")).toBe(action);
      expect(capturedBody.current!.get("radarrid")).toBe(String(radarrId));
      expect(capturedBody.current!.get("radarr_id")).toBeNull();
    });

    it("does not send radarrid for search-wanted action", async () => {
      const capturedBody = { current: null as FormData | null };

      server.use(
        http.patch("/api/movies", async ({ request }) => {
          capturedBody.current = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.movies.action({ action: "search-wanted" });

      expect(capturedBody.current).not.toBeNull();
      expect(capturedBody.current!.get("action")).toBe("search-wanted");
      expect(capturedBody.current!.get("radarrid")).toBeNull();
    });
  });
});
