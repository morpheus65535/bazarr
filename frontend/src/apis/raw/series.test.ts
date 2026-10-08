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

  describe("searchMissingSelected", () => {
    it("sends all ids in ONE request as a comma separated list", async () => {
      const bodies: FormData[] = [];

      server.use(
        http.patch("/api/series", async ({ request }) => {
          bodies.push(await request.formData());
          return new HttpResponse();
        }),
      );

      // Far above the server's per-request form-field cap: still one request.
      const ids = Array.from({ length: 2500 }, (_, i) => i + 1);
      await api.series.searchMissingSelected(ids);

      expect(bodies).toHaveLength(1);
      expect(bodies[0].get("action")).toBe("search-missing-selected");
      expect(bodies[0].get("seriesids")).toBe(ids.join(","));
    });

    it("sends whisper_fallback=false only when it is set", async () => {
      const bodies: FormData[] = [];

      server.use(
        http.patch("/api/series", async ({ request }) => {
          bodies.push(await request.formData());
          return new HttpResponse();
        }),
      );

      await api.series.searchMissingSelected([1], { whisperFallback: false });
      await api.series.searchMissingSelected([2], { whisperFallback: true });
      await api.series.searchMissingSelected([3]);

      expect(bodies[0].get("whisper_fallback")).toBe("false");
      expect(bodies[1].get("whisper_fallback")).toBe("true");
      expect(bodies[2].has("whisper_fallback")).toBe(false);
    });
  });
});
