import userEvent from "@testing-library/user-event";
import { describe, expect, it, vitest } from "vitest";
import { useSportsSubtitleModification } from "@/apis/hooks";
import { useModals } from "@/modules/modals";
import { customRender, screen } from "@/tests";
import { SportsSubtitle } from "./components";

vitest.mock("@/apis/hooks", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/apis/hooks")>();
  return {
    ...actual,
    useSportsSubtitleModification: vitest.fn(),
  };
});

vitest.mock("@/modules/modals", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/modules/modals")>();
  return { ...actual, useModals: vitest.fn() };
});

const mockUseSportsSubtitleModification = vitest.mocked(
  useSportsSubtitleModification,
);
const mockUseModals = vitest.mocked(useModals);

const externalSubtitle = {
  code2: "en",
  name: "English",
  hi: false,
  forced: false,
  path: "/subtitles/sub.srt",
  embeddedTrackId: null,
  id: 1,
} as Subtitle;

const embeddedSubtitle = {
  code2: "en",
  name: "English",
  hi: false,
  forced: false,
  path: null,
  embeddedTrackId: 1,
  id: 2,
} as Subtitle;

const renderSubtitle = (
  props?: Partial<React.ComponentProps<typeof SportsSubtitle>>,
) => {
  mockUseSportsSubtitleModification.mockReturnValue({
    download: { mutateAsync: vitest.fn() },
    remove: { mutateAsync: vitest.fn() },
  } as unknown as ReturnType<typeof useSportsSubtitleModification>);
  mockUseModals.mockReturnValue({
    openConfirmModal: vitest.fn(),
  } as unknown as ReturnType<typeof useModals>);

  customRender(
    <SportsSubtitle
      leagueId={1}
      eventId={2}
      subtitle={externalSubtitle}
      {...props}
    />,
  );
};

describe("SportsSubtitle", () => {
  it("offers delete for an external subtitle", async () => {
    renderSubtitle();

    await userEvent.hover(screen.getByText("en"));

    expect(await screen.findByText("Delete")).toBeInTheDocument();
  });

  it("offers search for a missing subtitle", async () => {
    renderSubtitle({ missing: true, subtitle: embeddedSubtitle });

    await userEvent.hover(screen.getByText("en"));

    expect(await screen.findByText("Search")).toBeInTheDocument();
  });

  it("attaches a menu to an external subtitle", () => {
    renderSubtitle();

    const badge = screen.getByText("en");

    // A menu target carries aria-haspopup, and no query matches on it.
    // eslint-disable-next-line testing-library/no-node-access
    expect(badge.closest("[aria-haspopup]")).not.toBeNull();
  });

  it("attaches no menu to an embedded subtitle", () => {
    renderSubtitle({ subtitle: embeddedSubtitle });

    const badge = screen.getByText("en");

    // eslint-disable-next-line testing-library/no-node-access
    expect(badge.closest("[aria-haspopup]")).toBeNull();
  });
});
