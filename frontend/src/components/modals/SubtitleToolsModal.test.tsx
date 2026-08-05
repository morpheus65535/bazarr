import React from "react";
import { beforeEach, describe, expect, it, vitest } from "vitest";
import {
  useEpisodeSubtitleModification,
  useMovieSubtitleModification,
} from "@/apis/hooks";
import SubtitleToolsMenu from "@/components/SubtitleToolsMenu";
import { customRender, waitFor } from "@/tests";
import { SubtitleToolView } from "./SubtitleToolsModal";

interface SimpleTableMockProps {
  data: Array<{ original: unknown }>;
  onRowSelectionChanged?: (rows: Array<{ original: unknown }>) => void;
}

vitest.mock("@/components/SubtitleToolsMenu", () => ({
  default: vitest.fn(),
}));

vitest.mock("@/components/tables/SimpleTable", async () => {
  const React = await import("react");
  const SimpleTableMock = (props: SimpleTableMockProps) => {
    const { data, onRowSelectionChanged } = props;
    const onRowSelectionChangedRef = React.useRef(onRowSelectionChanged);
    onRowSelectionChangedRef.current = onRowSelectionChanged;

    React.useEffect(() => {
      if (data.length > 0 && onRowSelectionChangedRef.current) {
        onRowSelectionChangedRef.current([{ original: data[0] }]);
      }
    }, [data]);

    return React.createElement(
      "div",
      { "data-testid": "simple-table" },
      "Mocked Table",
    );
  };

  return {
    default: SimpleTableMock,
  };
});

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useEpisodeSubtitleModification: vitest.fn(),
    useMovieSubtitleModification: vitest.fn(),
  };
});

const mockSubtitleToolsMenu = vitest.mocked(SubtitleToolsMenu);
const mockUseEpisodeSubtitleModification = vitest.mocked(
  useEpisodeSubtitleModification,
);
const mockUseMovieSubtitleModification = vitest.mocked(
  useMovieSubtitleModification,
);

const externalSubtitle = {
  code2: "en",
  name: "English",
  hi: false,
  forced: false,
  path: "/movies/movie.en.srt",
  embeddedTrackId: null,
  fileSize: 0,
  id: 42,
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
  subtitles: [externalSubtitle],
  missingSubtitles: [],
} as Item.Movie;

describe("SubtitleToolView", () => {
  beforeEach(() => {
    vitest.clearAllMocks();

    mockSubtitleToolsMenu.mockImplementation(() =>
      React.createElement("div", null, "Subtitle Tools Menu"),
    );

    mockUseEpisodeSubtitleModification.mockReturnValue({
      download: { mutateAsync: vitest.fn() },
      remove: { mutateAsync: vitest.fn() },
      upload: { mutateAsync: vitest.fn() },
    } as unknown as ReturnType<typeof useEpisodeSubtitleModification>);

    mockUseMovieSubtitleModification.mockReturnValue({
      download: { mutateAsync: vitest.fn() },
      remove: { mutateAsync: vitest.fn() },
      upload: { mutateAsync: vitest.fn() },
    } as unknown as ReturnType<typeof useMovieSubtitleModification>);
  });

  it("passes external subtitle selections with subtitlesId to SubtitleToolsMenu", async () => {
    customRender(<SubtitleToolView payload={[movie]} />);

    await waitFor(() => {
      expect(mockSubtitleToolsMenu).toHaveBeenCalled();
    });

    const lastCall = mockSubtitleToolsMenu.mock.calls.at(-1);
    expect(lastCall).toBeDefined();

    const selections = lastCall![0].selections;
    expect(selections).toHaveLength(1);
    expect(selections[0]).toMatchObject({
      id: 1,
      subtitlesId: 42,
      type: "movie",
      language: "en",
      path: "/movies/movie.en.srt",
      hi: "False",
      forced: "False",
    });
  });
});
