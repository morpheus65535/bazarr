import userEvent from "@testing-library/user-event";
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
      // eslint-disable-next-line testing-library/no-node-access
      button.closest("tr")?.textContent?.includes("New Subtitle Provider!"),
    );

    const nonDismissableButton = dismissButtons.find((button) =>
      // eslint-disable-next-line testing-library/no-node-access
      button.closest("tr")?.textContent?.includes("Python Deprecated!"),
    );

    expect(dismissableButton).not.toBeDisabled();
    expect(nonDismissableButton).toBeDisabled();
  });

  it("should render an announcement link", async () => {
    server.use(
      http.get("/api/system/announcements", () => {
        return HttpResponse.json({
          data: [
            {
              text: "Check the wiki",
              link: "https://wiki.bazarr.media",
              hash: "wiki-hash",
              dismissible: true,
              timestamp: "2024-01-01",
            },
          ],
        });
      }),
    );

    customRender(<SystemAnnouncementsView />);

    await waitFor(() => {
      expect(screen.getByText("Check the wiki")).toBeInTheDocument();
    });

    const link = screen.getByRole("link", { name: "Link" });

    expect(link).toHaveAttribute("href", "https://wiki.bazarr.media");
  });

  it("should dismiss an announcement", async () => {
    const dismissed = { current: false };

    server.use(
      http.get("/api/system/announcements", () => {
        return HttpResponse.json({
          data: dismissed.current
            ? []
            : [
                {
                  text: "Dismiss me",
                  link: "",
                  hash: "dismiss-hash",
                  dismissible: true,
                  timestamp: "2024-01-01",
                },
              ],
        });
      }),
      http.post("/api/system/announcements", async () => {
        dismissed.current = true;
        return HttpResponse.json({ data: [] });
      }),
    );

    customRender(<SystemAnnouncementsView />);

    await waitFor(() => {
      expect(screen.getByText("Dismiss me")).toBeInTheDocument();
    });

    await userEvent.click(
      screen.getByRole("button", { name: "Dismiss announcement" }),
    );

    await waitFor(() => {
      expect(screen.queryByText("Dismiss me")).not.toBeInTheDocument();
    });
  });
});
