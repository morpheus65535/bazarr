import { http } from "msw";
import { HttpResponse } from "msw";
import { customRender, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import SystemAnnouncementsView from ".";

describe("System Announcements", () => {
  it("should render with empty announcements", async () => {
    server.use(
      http.get("/api/system/announcements", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    customRender(<SystemAnnouncementsView />);

    await waitFor(() => {
      expect(
        screen.getByText(/No announcements for now, come back later!/i),
      ).toBeInTheDocument();
    });
  });

  it("should render with announcements", async () => {
    const mockAnnouncements = [
      {
        text: "New Subtitle Provider!",
        dismissible: true,
      },
      {
        text: "Python Deprecated!",
        dismissible: false,
      },
    ];

    server.use(
      http.get("/api/system/announcements", () => {
        return HttpResponse.json({
          data: mockAnnouncements,
        });
      }),
    );

    customRender(<SystemAnnouncementsView />);

    await waitFor(() => {
      expect(screen.getByText("New Subtitle Provider!")).toBeInTheDocument();
    });

    expect(screen.getByText("Python Deprecated!")).toBeInTheDocument();

    const dismissButtons = screen.getAllByLabelText("Dismiss announcement");

    const dismissableButton = dismissButtons.find((button) =>
      button.closest("tr")?.textContent?.includes("New Subtitle Provider!"),
    );

    const nonDismissableButton = dismissButtons.find((button) =>
      button.closest("tr")?.textContent?.includes("Python Deprecated!"),
    );

    expect(dismissableButton).not.toBeDisabled();
    expect(nonDismissableButton).toBeDisabled();
  });
});
