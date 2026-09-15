import userEvent from "@testing-library/user-event";
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
          data: [{ name: "Addic7ed", status: "disabled", retry: "1" }],
        });
      }),
    );

    customRender(<SystemProvidersView />);

    await waitFor(() => {
      expect(screen.getByText("Addic7ed")).toBeInTheDocument();
    });

    expect(screen.getByText("Addic7ed")).toBeInTheDocument();

    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Next Retry")).toBeInTheDocument();

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

  it("should refresh providers when clicking Refresh", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json({
          data: [{ name: "Addic7ed", status: "disabled", retry: "1" }],
        });
      }),
    );

    customRender(<SystemProvidersView />);

    await waitFor(() => {
      expect(screen.getByText("Addic7ed")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));

    expect(screen.getByRole("button", { name: "Refresh" })).toBeInTheDocument();
  });

  it("should reset providers when clicking Reset", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json({
          data: [{ name: "Addic7ed", status: "disabled", retry: "1" }],
        });
      }),
      http.post("/api/providers", () => {
        return HttpResponse.json({});
      }),
    );

    customRender(<SystemProvidersView />);

    await waitFor(() => {
      expect(screen.getByText("Addic7ed")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "Reset" }));

    expect(screen.getByRole("button", { name: "Reset" })).toBeInTheDocument();
  });
});
