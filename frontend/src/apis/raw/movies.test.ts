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

  describe("searchMissingSelected", () => {
    it("sends all ids in ONE request as a comma separated list", async () => {
      const bodies: FormData[] = [];

      server.use(
        http.patch("/api/movies", async ({ request }) => {
          bodies.push(await request.formData());
          return new HttpResponse();
        }),
      );

      // Far above the server's per-request form-field cap: still one request.
      const ids = Array.from({ length: 2500 }, (_, i) => i + 1);
      await api.movies.searchMissingSelected(ids);

      expect(bodies).toHaveLength(1);
      expect(bodies[0].get("action")).toBe("search-missing-selected");
      expect(bodies[0].get("radarrids")).toBe(ids.join(","));
    });
  });
});
