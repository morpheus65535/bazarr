import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { customRender, screen } from "@/tests";
import SportsLeaguePosterCard from "./PosterCard";

const league = {
  sportarrLeagueId: 4,
  title: "UFC",
  sport: "Fighting",
  poster: "",
  monitored: true,
  profileId: 1,
  episodeFileCount: 4,
  episodeMissingCount: 1,
} as Item.SportsLeague;

describe("SportsLeaguePosterCard", () => {
  it("shows a tooltip on the monitored icon", async () => {
    const { container } = customRender(
      <SportsLeaguePosterCard item={league} onEdit={vitest.fn()} />,
    );

    // The icon is decorative, so no role query reaches it.
    // eslint-disable-next-line testing-library/no-container, testing-library/no-node-access
    const icon = container.querySelector('[data-icon="bookmark"]');
    expect(icon).not.toBeNull();
    await userEvent.hover(icon!);

    expect(await screen.findByText("Monitored")).toBeInTheDocument();
  });

  it("counts files in the progress tooltip", async () => {
    customRender(<SportsLeaguePosterCard item={league} onEdit={vitest.fn()} />);

    await userEvent.hover(screen.getByRole("progressbar"));

    expect(
      await screen.findByText("Files with subtitles: 3/4"),
    ).toBeInTheDocument();
  });
});
