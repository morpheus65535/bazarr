import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import api from "@/apis/raw";
import server from "@/tests/mocks/node";

describe("SeriesApi", () => {
  describe("action", () => {
    it.each([
      ["search-missing", 1],
      ["scan-disk", 2],
      ["sync", 3],
    ] as const)("sends seriesid for '%s' action", async (action, seriesId) => {
      const capturedBody = { current: null as FormData | null };

      server.use(
        http.patch("/api/series", async ({ request }) => {
          capturedBody.current = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.series.action({ action, seriesId });

      expect(capturedBody.current).not.toBeNull();
      expect(capturedBody.current!.get("action")).toBe(action);
      expect(capturedBody.current!.get("seriesid")).toBe(String(seriesId));
      expect(capturedBody.current!.get("series_id")).toBeNull();
    });

    it("does not send seriesid for search-wanted action", async () => {
      const capturedBody = { current: null as FormData | null };

      server.use(
        http.patch("/api/series", async ({ request }) => {
          capturedBody.current = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.series.action({ action: "search-wanted" });

      expect(capturedBody.current).not.toBeNull();
      expect(capturedBody.current!.get("action")).toBe("search-wanted");
      expect(capturedBody.current!.get("seriesid")).toBeNull();
    });
  });
});
