/* eslint-disable camelcase */
import { http } from "msw";
import { HttpResponse } from "msw";
import { render, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import MoviesHistoryView from ".";

const mockMovieHistory = {
  data: [
    {
      action: "download",
      title: "The Dark Knight (2008) [1080p.BluRay.x264.DTS-HD.MA.5.1]",
      radarrId: 1,
      language: { code2: "en", name: "English" },
      score: 0.95,
      matches: ["scene", "release"],
      dont_matches: [],
      timestamp: "2024-03-20T10:00:00Z",
      parsed_timestamp: "March 20, 2024 10:00:00",
      description: "Test description",
      upgradable: true,
      blacklisted: false,
      provider: "opensubtitles",
      subs_id: "123",
      subtitles_path: "/path/to/subtitles.srt",
    },
  ],
  total: 1,
  page: 1,
  per_page: 10,
};

describe("History Movies", () => {
  beforeEach(() => {
    server.use(
      http.get("/api/movies/history", () => {
        return HttpResponse.json(mockMovieHistory);
      }),
      http.get("/api/providers", () => {
        return HttpResponse.json({
          data: ["test-provider"],
        });
      }),
      http.get("/api/system/languages", () => {
        return HttpResponse.json({
          en: { code2: "en", name: "English" },
        });
      }),
    );
  });

  it("should render the movies history table", async () => {
    render(<MoviesHistoryView />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "The Dark Knight (2008) [1080p.BluRay.x264.DTS-HD.MA.5.1]",
        ),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Language")).toBeInTheDocument();
    expect(screen.getByText("Score")).toBeInTheDocument();
    expect(screen.getByText("Match")).toBeInTheDocument();
    expect(screen.getByText("Date")).toBeInTheDocument();
    expect(screen.getByText("Info")).toBeInTheDocument();
    expect(screen.getByText("Upgradable")).toBeInTheDocument();
    expect(screen.getByText("Blacklist")).toBeInTheDocument();
  });

  it("should display movie information correctly", async () => {
    render(<MoviesHistoryView />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "The Dark Knight (2008) [1080p.BluRay.x264.DTS-HD.MA.5.1]",
        ),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("English")).toBeInTheDocument();
    expect(screen.getByText("0.95")).toBeInTheDocument();
  });

  it("should show blacklist button when movie is not blacklisted", async () => {
    render(<MoviesHistoryView />);

    await waitFor(() => {
      expect(screen.getByLabelText("Add to Blacklist")).toBeInTheDocument();
    });
  });

  it("should show empty state when no history is found", async () => {
    server.use(
      http.get("/api/movies/history", () => {
        return HttpResponse.json({
          data: [],
          total: 0,
          page: 1,
          per_page: 10,
        });
      }),
    );

    render(<MoviesHistoryView />);

    await waitFor(() => {
      expect(
        screen.getByText("Nothing Found in Movies History"),
      ).toBeInTheDocument();
    });
  });

  it("should navigate to movie details when clicking on movie title", async () => {
    render(<MoviesHistoryView />);

    await waitFor(() => {
      const movieLink = screen.getByText(
        "The Dark Knight (2008) [1080p.BluRay.x264.DTS-HD.MA.5.1]",
      );
      expect(movieLink).toHaveAttribute("href", "/movies/1");
    });
  });
});
