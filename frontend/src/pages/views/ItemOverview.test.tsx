import { http, HttpResponse } from "msw";
import { describe, it } from "vitest";
import { customRender, screen } from "@/tests";
import server from "@/tests/mocks/node";
import ItemOverview from "./ItemOverview";

const createMinimalItem = (overrides: Partial<Item.Base> = {}): Item.Base =>
  ({
    id: "1",
    title: "Test Movie",
    path: "/movies/test",
    fanart: "",
    poster: "",
    monitored: true,
    tags: [],
    alternativeTitles: [],
    audio_language: [],
    profileId: undefined,
    overview: "Test overview",
    ...overrides,
  }) as Item.Base;

describe("ItemOverview", () => {
  it("should render without crashing", () => {
    server.use(
      http.get("/api/system/languages/profiles", () => {
        return HttpResponse.json([]);
      }),
      http.get("/api/system/languages", () => {
        return HttpResponse.json({ languages: [] });
      }),
    );

    const item = createMinimalItem();
    customRender(<ItemOverview item={item} />);

    expect(screen.getByText("Test Movie")).toBeInTheDocument();
  });
});
