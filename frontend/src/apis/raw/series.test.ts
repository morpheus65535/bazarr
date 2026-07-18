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
      let capturedBody: FormData | null = null;

      server.use(
        http.patch("/api/series", async ({ request }) => {
          capturedBody = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.series.action({ action, seriesId });

      expect(capturedBody).not.toBeNull();
      expect(capturedBody!.get("action")).toBe(action);
      expect(capturedBody!.get("seriesid")).toBe(String(seriesId));
      expect(capturedBody!.get("series_id")).toBeNull();
    });

    it("does not send seriesid for search-wanted action", async () => {
      let capturedBody: FormData | null = null;

      server.use(
        http.patch("/api/series", async ({ request }) => {
          capturedBody = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.series.action({ action: "search-wanted" });

      expect(capturedBody).not.toBeNull();
      expect(capturedBody!.get("action")).toBe("search-wanted");
      expect(capturedBody!.get("seriesid")).toBeNull();
    });
  });
});
