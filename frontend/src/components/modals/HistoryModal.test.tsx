import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import { MovieHistoryModal } from "./HistoryModal";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useMovieHistory: vitest.fn(),
    useMovieAddBlacklist: vitest.fn(),
  };
});

const mockUseMovieHistory = vitest.mocked(
  (await import("@/apis/hooks")).useMovieHistory,
);
const mockUseMovieAddBlacklist = vitest.mocked(
  (await import("@/apis/hooks")).useMovieAddBlacklist,
);

const movie = { radarrId: 5, title: "Test Movie" } as Item.Movie;

const historyEntry = {
  action: 1,
  language: { code2: "en", name: "English" },
  provider: "OpenSubtitles",
  score: 100,
  matches: ["match1"],
  dontMatches: [],
  timestamp: "2024-01-01T00:00:00",
  parsedTimestamp: "January 1, 2024",
  blacklisted: false,
  radarrId: 5,
  subsId: 123,
  subtitlesPath: "/path/to/sub.srt",
} as unknown as History.Movie;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const context = {} as any;

describe("HistoryModal", () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it("renders movie history with entries", async () => {
    mockUseMovieHistory.mockReturnValue({
      data: [historyEntry],
      isFetching: false,
      refetch: vitest.fn(),
    } as unknown as ReturnType<typeof mockUseMovieHistory>);
    mockUseMovieAddBlacklist.mockReturnValue({
      mutate: vitest.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof mockUseMovieAddBlacklist>);

    customRender(
      <MovieHistoryModal context={context} id="test" innerProps={{ movie }} />,
    );

    expect(await screen.findByText("OpenSubtitles")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("2024-01-01T00:00:00")).toBeInTheDocument();
  });

  it("shows blacklist button for entries with subsId", async () => {
    mockUseMovieHistory.mockReturnValue({
      data: [historyEntry],
      isFetching: false,
      refetch: vitest.fn(),
    } as unknown as ReturnType<typeof mockUseMovieHistory>);
    const addBlacklist = vitest.fn();
    mockUseMovieAddBlacklist.mockReturnValue({
      mutate: addBlacklist,
      isPending: false,
    } as unknown as ReturnType<typeof mockUseMovieAddBlacklist>);

    customRender(
      <MovieHistoryModal context={context} id="test" innerProps={{ movie }} />,
    );

    expect(
      await screen.findByRole("button", { name: "Add to Blacklist" }),
    ).toBeInTheDocument();
  });

  it("renders the empty state when there is no history", async () => {
    mockUseMovieHistory.mockReturnValue({
      data: undefined,
      isFetching: false,
      refetch: vitest.fn(),
    } as unknown as ReturnType<typeof mockUseMovieHistory>);
    mockUseMovieAddBlacklist.mockReturnValue({
      mutate: vitest.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof mockUseMovieAddBlacklist>);

    customRender(
      <MovieHistoryModal context={context} id="test" innerProps={{ movie }} />,
    );

    expect(await screen.findByText("No history found")).toBeInTheDocument();
  });

  it("renders history without language", async () => {
    const entryWithoutLang = { ...historyEntry, language: undefined };

    mockUseMovieHistory.mockReturnValue({
      data: [entryWithoutLang],
      isFetching: false,
      refetch: vitest.fn(),
    } as unknown as ReturnType<typeof mockUseMovieHistory>);
    mockUseMovieAddBlacklist.mockReturnValue({
      mutate: vitest.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof mockUseMovieAddBlacklist>);

    customRender(
      <MovieHistoryModal context={context} id="test" innerProps={{ movie }} />,
    );

    expect(await screen.findByText("100")).toBeInTheDocument();
  });
});
