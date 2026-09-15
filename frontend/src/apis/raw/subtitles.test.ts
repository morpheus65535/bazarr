import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import api from "@/apis/raw";
import server from "@/tests/mocks/node";

describe("SubtitlesApi", () => {
  describe("modify", () => {
    it("strips null values from the form payload", async () => {
      const capturedBody = { current: null as FormData | null };

      server.use(
        http.patch("/api/subtitles", async ({ request }) => {
          capturedBody.current = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.subtitles.modify("extract", {
        id: 1,
        subtitlesId: 2,
        type: "episode",
        language: "en",
        path: null,
        mediaTitle: "Episode Title",
        hi: "False",
        forced: "False",
      });

      expect(capturedBody.current).not.toBeNull();
      expect(capturedBody.current!.get("id")).toBe("1");
      expect(capturedBody.current!.get("media_id")).toBeNull();
      expect(capturedBody.current!.get("subtitles_id")).toBe("2");
      expect(capturedBody.current!.get("type")).toBe("episode");
      expect(capturedBody.current!.get("language")).toBe("en");
      expect(capturedBody.current!.get("media_title")).toBeNull();
      expect(capturedBody.current!.get("path")).toBeNull();
      expect(capturedBody.current!.get("hi")).toBe("False");
      expect(capturedBody.current!.get("forced")).toBe("False");
    });

    it("sends non-null path values", async () => {
      const capturedBody = { current: null as FormData | null };

      server.use(
        http.patch("/api/subtitles", async ({ request }) => {
          capturedBody.current = await request.formData();
          return new HttpResponse();
        }),
      );

      await api.subtitles.modify("sync", {
        id: 1,
        subtitlesId: 2,
        type: "episode",
        language: "en",
        path: "/subtitles/sub.srt",
        hi: "False",
        forced: "False",
      });

      expect(capturedBody.current).not.toBeNull();
      expect(capturedBody.current!.get("path")).toBe("/subtitles/sub.srt");
    });
  });
});
