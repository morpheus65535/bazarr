import { useMediaQuery } from "@mantine/hooks";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen, waitFor } from "@/tests";
import StateIcon from "./StateIcon";

vitest.mock("@mantine/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@mantine/hooks")>();
  return { ...actual, useMediaQuery: vitest.fn() };
});

const mockUseMediaQuery = vitest.mocked(useMediaQuery);

describe("StateIcon", () => {
  beforeEach(() => {
    mockUseMediaQuery.mockReturnValue(false);
  });

  async function openPopover(container: HTMLElement) {
    // eslint-disable-next-line testing-library/no-node-access
    const svg = container.querySelector("svg");
    expect(svg).toBeTruthy();
    await userEvent.click(svg!);
  }

  it("renders the ok icon variant and popover matches", async () => {
    const { container } = customRender(
      <StateIcon matches={["Match"]} dont={[]} isHistory={false} />,
    );

    await openPopover(container);

    await waitFor(() => {
      expect(screen.getByText("Matching")).toBeInTheDocument();
      expect(screen.getByText("Match")).toBeInTheDocument();
    });
  });

  it("renders the issue icon variant and popover misses", async () => {
    const { container } = customRender(
      <StateIcon matches={[]} dont={["Miss"]} isHistory={false} />,
    );

    await openPopover(container);

    await waitFor(() => {
      expect(screen.getByText("Not Matching")).toBeInTheDocument();
      expect(screen.getByText("Miss")).toBeInTheDocument();
    });
  });

  it("renders the history icon variant", async () => {
    const { container } = customRender(
      <StateIcon matches={[]} dont={[]} isHistory={true} />,
    );

    await openPopover(container);

    await waitFor(() => {
      expect(screen.getByText("Scoring Criteria")).toBeInTheDocument();
    });
  });

  it("uses mobile layout when viewport is small", async () => {
    mockUseMediaQuery.mockReturnValue(true);

    const { container } = customRender(
      <StateIcon matches={["Match"]} dont={[]} isHistory={false} />,
    );

    await openPopover(container);

    await waitFor(() => {
      expect(screen.getByText("Matching")).toBeInTheDocument();
    });
  });
});
