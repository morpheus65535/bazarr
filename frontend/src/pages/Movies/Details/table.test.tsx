import { describe, expect, it, vitest } from "vitest";
import { useMovieSubtitleModification } from "@/apis/hooks";
import { useShowOnlyDesired } from "@/apis/hooks/site";
import { customRender, screen } from "@/tests";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import Table from "./table";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return { ...actual, useMovieSubtitleModification: vitest.fn() };
});

vitest.mock("@/apis/hooks/site", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks/site")>();
  return { ...actual, useShowOnlyDesired: vitest.fn() };
});

vitest.mock("@/utilities/languages", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/utilities/languages")>();
  return { ...actual, useProfileItemsToLanguages: vitest.fn() };
});

const mockUseMovieSubtitleModification = vitest.mocked(
  useMovieSubtitleModification,
);
const mockUseShowOnlyDesired = vitest.mocked(useShowOnlyDesired);
const mockUseProfileItemsToLanguages = vitest.mocked(
  useProfileItemsToLanguages,
);

const externalSubtitle = {
  code2: "en",
  name: "English",
  hi: false,
  forced: false,
  path: "/subtitles/sub.srt",
  embeddedTrackId: null,
  fileSize: 0,
  id: 1,
} as Subtitle;

const embeddedSubtitle = {
  code2: "fr",
  name: "French",
  hi: false,
  forced: false,
  path: null,
  embeddedTrackId: 1,
  fileSize: 0,
  id: 2,
} as Subtitle;

const movie = {
  radarrId: 1,
  title: "Movie Title",
  path: "/movies/movie.mkv",
  monitored: true,
  audioLanguage: [],
  profileId: 1,
  fanart: "",
  overview: "",
  imdbId: "tt123",
  alternativeTitles: [],
  poster: "",
  year: "2024",
  tags: [],
  sceneName: "",
  subtitles: [externalSubtitle, embeddedSubtitle],
  missingSubtitles: [],
} as Item.Movie;

const renderTable = (props?: Partial<React.ComponentProps<typeof Table>>) => {
  mockUseMovieSubtitleModification.mockReturnValue({
    download: { mutateAsync: vitest.fn(), isPending: false },
    remove: { mutateAsync: vitest.fn(), isPending: false },
    upload: { mutateAsync: vitest.fn(), isPending: false },
  } as unknown as ReturnType<typeof useMovieSubtitleModification>);
  mockUseShowOnlyDesired.mockReturnValue(false);
  mockUseProfileItemsToLanguages.mockReturnValue([]);

  customRender(<Table movie={movie} {...props} />);
};

describe("MovieDetailsTable", () => {
  it("renders external and embedded subtitles", () => {
    renderTable();
    expect(screen.getByText("Video File Subtitle Track")).toBeInTheDocument();
    expect(screen.getByText("/subtitles/sub.srt")).toBeInTheDocument();
  });
});
