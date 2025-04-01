import { http } from "msw";
import { HttpResponse } from "msw";
import { render, screen } from "@/tests";
import server from "@/tests/mocks/node";
import SystemReleasesView from ".";

describe("System Releases", () => {
  it("should render with releases", async () => {
    const mockReleases = [
      {
        name: "v1.0.0",
        body: [
          "Added support for embedded subtitles in MKV files",
          "Improved subtitle synchronization accuracy",
        ],
        date: "2024-03-20",
        prerelease: false,
        current: true,
      },
      {
        name: "v1.1.0-beta",
        body: [
          "Added support for multiple subtitle providers",
          "Enhanced subtitle language detection",
        ],
        date: "2024-03-21",
        prerelease: true,
        current: false,
      },
    ];

    server.use(
      http.get("/api/system/releases", () => {
        return HttpResponse.json({
          data: mockReleases,
        });
      }),
    );

    render(<SystemReleasesView />);

    await screen.findByText("v1.0.0");
    await screen.findByText("v1.1.0-beta");

    expect(screen.getByText("v1.0.0")).toBeInTheDocument();
    expect(screen.getByText("v1.1.0-beta")).toBeInTheDocument();
    expect(screen.getByText("2024-03-20")).toBeInTheDocument();
    expect(screen.getByText("2024-03-21")).toBeInTheDocument();
    expect(screen.getByText("Master")).toBeInTheDocument();
    expect(screen.getByText("Development")).toBeInTheDocument();
    expect(screen.getByText("Installed")).toBeInTheDocument();
    expect(
      screen.getByText("Added support for embedded subtitles in MKV files"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Improved subtitle synchronization accuracy"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Added support for multiple subtitle providers"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Enhanced subtitle language detection"),
    ).toBeInTheDocument();
  });

  it("should render empty state when no releases", async () => {
    server.use(
      http.get("/api/system/releases", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    render(<SystemReleasesView />);

    expect(screen.queryByRole("card")).not.toBeInTheDocument();
  });
});
