/* eslint-disable camelcase */
import { http } from "msw";
import { HttpResponse } from "msw";
import { customRender, screen, waitFor } from "@/tests";
import server from "@/tests/mocks/node";
import SystemTasksView from ".";

describe("System Tasks", () => {
  it("should render without tasks", async () => {
    server.use(
      http.get("/api/system/tasks", () => {
        return HttpResponse.json({
          data: [],
        });
      }),
    );

    customRender(<SystemTasksView />);

    await waitFor(() => {
      expect(screen.getByText("Refresh")).toBeInTheDocument();
    });
  });

  it("should render with system tasks", async () => {
    const mockTasks = [
      {
        name: "Scan Series",
        interval: "1 hour",
        next_run_in: "30 minutes",
        job_id: "series_scan",
        job_running: false,
      },
      {
        name: "Scan Movies",
        interval: "1 hour",
        next_run_in: "45 minutes",
        job_id: "movies_scan",
        job_running: true,
      },
    ];

    server.use(
      http.get("/api/system/tasks", () => {
        return HttpResponse.json({
          data: mockTasks,
        });
      }),
    );

    customRender(<SystemTasksView />);

    await waitFor(() => {
      expect(screen.getByText("Scan Series")).toBeInTheDocument();
    });

    expect(screen.getByText("Scan Movies")).toBeInTheDocument();
    expect(screen.getByText("30 minutes")).toBeInTheDocument();
    expect(screen.getByText("45 minutes")).toBeInTheDocument();

    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Interval")).toBeInTheDocument();
    expect(screen.getByText("Next Execution")).toBeInTheDocument();
    expect(screen.getByText("Run")).toBeInTheDocument();

    const runButtons = screen.getAllByLabelText("Run Job");
    expect(runButtons).toHaveLength(2);
  });
});
