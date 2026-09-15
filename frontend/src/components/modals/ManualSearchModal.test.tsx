import { UseQueryResult } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import { MovieSearchModal } from "./ManualSearchModal";

const item = {
  radarrId: 5,
  title: "Movie Title",
  path: "/movie/path",
  sceneName: "movie.scene",
} as Item.Movie;

const searchResult = {
  score: 85,
  language: "en",
  hearingImpaired: "False",
  forced: "False",
  provider: "My Provider",
  url: "https://example.com",
  releaseInfo: ["Main release info", "Detail 1", "Detail 2"],
  matches: ["match1"],
  dontMatches: [],
  subtitle: {},
  uploader: "uploader1",
  originalFormat: "True",
  scoreWithoutHash: 0,
} as unknown as SearchResultType;

describe("ManualSearchModal", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  const createMockQuery = (
    results: SearchResultType[] | undefined,
    isFetching = false,
  ) =>
    ({
      data: results,
      isFetching,
      refetch: vitest.fn(),
    }) as unknown as UseQueryResult<SearchResultType[] | undefined>;

  it("renders the item info and search button", () => {
    const query = vitest.fn().mockReturnValue(createMockQuery(undefined));
    const download = vitest.fn();

    customRender(
      <MovieSearchModal
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        context={{} as any}
        id="test"
        innerProps={{ item, query, download }}
      />,
    );

    expect(screen.getByText("/movie/path")).toBeInTheDocument();
    expect(screen.getByText("Search")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
  });

  it("triggers a search when the button is clicked", async () => {
    const query = vitest
      .fn()
      .mockReturnValue(createMockQuery([searchResult], false));
    const download = vitest.fn();

    customRender(
      <MovieSearchModal
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        context={{} as any}
        id="test"
        innerProps={{ item, query, download }}
      />,
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(screen.getByText("Search Again")).toBeInTheDocument();
  });

  it("renders search results and allows download", async () => {
    const query = vitest
      .fn()
      .mockReturnValue(createMockQuery([searchResult], false));
    const download = vitest.fn();

    customRender(
      <MovieSearchModal
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        context={{} as any}
        id="test"
        innerProps={{ item, query, download }}
      />,
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Search" }));
    await user.click(screen.getAllByRole("button", { name: "Download" })[0]);

    expect(download).toHaveBeenCalledWith(item, searchResult);
  });

  it("shows search again button after first search", async () => {
    const query = vitest
      .fn()
      .mockReturnValue(createMockQuery(undefined, false));
    const download = vitest.fn();

    customRender(
      <MovieSearchModal
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        context={{} as any}
        id="test"
        innerProps={{ item, query, download }}
      />,
    );

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(screen.getByText("Search Again")).toBeInTheDocument();
  });
});
