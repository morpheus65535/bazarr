import { http } from "msw";
import { HttpResponse } from "msw";
import { customRender, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import SystemProvidersView from ".";

describe("System Providers", () => {
  it("should render with providers", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json({
          data: [
            { name: "OpenSubtitles", status: "active", retry: "0" },
            { name: "Subscene", status: "inactive", retry: "3" },
            { name: "Addic7ed", status: "disabled", retry: "1" },
          ],
        });
      }),
    );

    customRender(<SystemProvidersView />);

    await waitFor(() => {
      expect(screen.getByText("OpenSubtitles")).toBeInTheDocument();
    });

    expect(screen.getByText("OpenSubtitles")).toBeInTheDocument();
    expect(screen.getByText("Subscene")).toBeInTheDocument();
    expect(screen.getByText("Addic7ed")).toBeInTheDocument();

    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("inactive")).toBeInTheDocument();
    expect(screen.getByText("disabled")).toBeInTheDocument();

    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();

    // Verify toolbar buttons are present
    expect(screen.getByText("Refresh")).toBeInTheDocument();
    expect(screen.getByText("Reset")).toBeInTheDocument();
  });

  it("should render with no providers", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    customRender(<SystemProvidersView />);
  });
});
