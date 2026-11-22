import { http, HttpResponse } from "msw/http";
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
    audioLanguage: [],
    profileId: undefined,
    overview: "Test overview",
    ...overrides,
  }) as Item.Base;

// A profile item as the languages profiles endpoint returns it (snake case, before camel-casing).
const rawItem = (
  id: number,
  language: string,
  overrides: Record<string, string> = {},
) => ({
  id,
  language,
  audio_exclude: "False",
  audio_only_include: "False",
  hi: "False",
  forced: "False",
  ...overrides,
});

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

  it("should show an enhanced profile as its rules expression", async () => {
    server.use(
      http.get("/api/system/languages/profiles", () => {
        return HttpResponse.json([
          {
            profileId: 2,
            name: "Series Rule",
            tag: null,
            cutoff: 1,
            profileType: "enhanced",
            items: [
              rawItem(1, "en"),
              rawItem(2, "fr"),
              rawItem(3, "de"),
              rawItem(4, "it"),
            ],
            groups: [
              {
                id: 1,
                operator: "AND",
                items: [rawItem(1, "en"), rawItem(2, "fr")],
              },
              {
                id: 2,
                operator: "OR",
                items: [rawItem(3, "de"), rawItem(4, "it")],
              },
            ],
            mustContain: [],
            mustNotContain: [],
            originalFormat: false,
          },
        ]);
      }),
    );

    customRender(<ItemOverview item={createMinimalItem({ profileId: 2 })} />);

    expect(await screen.findByText("Series Rule")).toBeInTheDocument();
    expect(screen.getByText("All of")).toBeInTheDocument();
    expect(screen.getByText("Any of")).toBeInTheDocument();
    expect(screen.getByText("de")).toBeInTheDocument();
  });

  it("should show a basic profile's languages and highlight its cutoff", async () => {
    server.use(
      http.get("/api/system/languages/profiles", () => {
        return HttpResponse.json([
          {
            profileId: 3,
            name: "Basic Rule",
            tag: null,
            cutoff: 2,
            profileType: "basic",
            items: [rawItem(1, "en"), rawItem(2, "fr", { hi: "True" })],
            mustContain: [],
            mustNotContain: [],
            originalFormat: false,
          },
        ]);
      }),
    );

    customRender(<ItemOverview item={createMinimalItem({ profileId: 3 })} />);

    expect(await screen.findByText("Basic Rule")).toBeInTheDocument();
    expect(screen.getByText("fr:HI")).toBeInTheDocument();
    const cutoffBadge = screen.getByTitle("Stops searching once this is found");
    expect(cutoffBadge).toHaveTextContent("fr:HI");
  });
});
